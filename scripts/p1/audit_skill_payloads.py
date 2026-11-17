#!/usr/bin/env python3
"""Read-only, binary-safe recursive audit of pinned AI skill payloads."""
from __future__ import annotations
import argparse, concurrent.futures, csv, hashlib, json, re, time, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

def read_csv(p):
    with p.open(newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f))

def git_blob_sha1(raw):
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii")+raw).hexdigest()

def url_for(repo, commit, path):
    return "https://raw.githubusercontent.com/"+repo+"/"+commit+"/"+"/".join(urllib.parse.quote(x,safe="") for x in path.split("/"))

def fetch(repo, commit, path, timeout, retries):
    url=url_for(repo,commit,path); req=urllib.request.Request(url,headers={"User-Agent":"MoreAI-P1-Payload-Audit/1.0"})
    error="FETCH_FAILED"
    for n in range(retries+1):
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r: return r.read(),"FETCHED"
        except urllib.error.HTTPError as e:
            error=f"HTTP_{e.code}"
            if e.code not in (408,425,429,500,502,503,504): break
        except Exception as e: error=f"{type(e).__name__}: {e}"
        if n<retries: time.sleep(min(2**n,8))
    return None,error

def norm(p):
    parts=[]
    for x in PurePosixPath(p).parts:
        if x in ("","."): continue
        if x=="..":
            if parts: parts.pop()
        else: parts.append(x)
    return "/".join(parts)

def refs(text, path):
    ext=PurePosixPath(path).suffix.lower()
    pats=[]
    if ext in {".md",".mdx",".rst",".txt"}:
        pats.append(r"\]\(([^)]+)\)")
    if ext in {".html",".htm",".md",".mdx"}:
        pats.append(r"<(?:img|script|source|link)[^>]+(?:src|href)=['\"]([^'\"]+)['\"]")
    if ext in {".js",".mjs",".jsx",".ts",".tsx"}:
        pats += [r"(?:from|import)\s+['\"](\.{1,2}/[^'\"]+)['\"]",
                 r"(?:require|import)\s*\(\s*['\"](\.{1,2}/[^'\"]+)['\"]",
                 r"(?:src|href)\s*=\s*['\"](\.{1,2}/[^'\"]+)['\"]"]
    if ext==".py":
        pats.append(r"^\s*from\s+(\.{1,3}[\w.]*)\s+import\s+")
    return list(dict.fromkeys(m.group(1).strip() for pat in pats for m in re.finditer(pat,text,re.I|re.M)))


def resolve(current, ref, known):
    v=ref.strip().strip("<>").strip("'\"").split("#",1)[0].split("?",1)[0]
    if not v or v.startswith(("http://","https://","mailto:","data:","javascript:","#")): return None
    candidates=[norm(str(PurePosixPath(current).parent/v)),norm(v)]
    expanded=[]
    for c in candidates:
        expanded += [c]
        if not PurePosixPath(c).suffix:
            expanded += [c+".md",c+".py",c+".json",c+".yaml",c+".yml",c.rstrip("/")+"/SKILL.md",c.rstrip("/")+"/README.md"]
    return next((x for x in expanded if x in known),None)

def classify(path):
    p=PurePosixPath(path); name=p.name.lower(); ext=p.suffix.lower()
    if name in {"license","license.txt","licence","licence.txt","copying","notice","notice.txt"}: return "license-notice","copy","Preserve notice verbatim; verify scope and attribution"
    if name=="skill.md": return "skill-entrypoint","adapt","Review safety, provenance and attribution"
    if name in {".gitignore", ".luaurc", ".styluaignore"}: return "configuration-or-schema","adapt","Review build and runtime configuration"
    if ext in {".woff",".woff2",".ttf",".otf",".eot"}: return "font-asset","defer","Verify font redistribution and embedding rights"
    if ext in {".png",".jpg",".jpeg",".webp",".gif",".svg",".mp4",".mov",".webm",".mp3",".wav",".ogg",".glb",".gltf",".obj",".fbx",".blend",".zip",".pdf"}: return "media-or-binary-asset","defer","Inspect bytes, provenance, license and malware status"
    if ext in {".py",".js",".mjs",".jsx",".ts",".tsx",".sh",".bash",".c",".cpp",".h",".gd",".gdshader",".hlsl",".glsl",".luau",".lua",".cs",".compute",".uss",".tss"}: return "executable-source","defer","Security, relevance, sandbox and architecture review required before adaptation"
    if ext in {".md",".mdx",".txt",".rst"}: return "reference-document","adapt","Review citations, third-party content and prompt safety"
    if ext in {".json",".yaml",".yml",".toml",".cfg",".ini",".xml",".asmdef",".gdextension"}: return "configuration-or-schema","defer","Dependency, schema, secret and runtime review required before adaptation"
    if re.search(r"(^|/)(test|tests|fixtures|examples|example|demo|samples)(/|$)",path,re.I): return "test-example-fixture","archive-only","Retain provenance; not production runtime by default"
    return "other","defer","Manual content, purpose and rights review required"

STATIC_PATTERNS = {
    "dynamic_code": re.compile(r"\\b(?:eval|exec|compile)\\s*\\(|\\bnew\\s+Function\\s*\\(", re.I),
    "process_spawn": re.compile(r"\\b(?:subprocess\\.(?:Popen|run|call|check_call|check_output)|os\\.(?:system|popen|execv\\w*)|child_process|execSync|spawnSync|spawn)\\b", re.I),
    "network_io": re.compile(r"\\b(?:fetch\\s*\\(|axios\\.|requests\\.(?:get|post|put|delete)|httpx\\.|urllib\\.request|WebSocket|socket\\.connect|https?://)", re.I),
    "credential_or_environment": re.compile(r"\\b(?:API[_-]?KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL|os\\.environ|getenv\\s*\\(|process\\.env)\\b", re.I),
    "filesystem_mutation": re.compile(r"\\b(?:writeFile(?:Sync)?|unlink(?:Sync)?|rmdir(?:Sync)?|mkdir(?:Sync)?|shutil\\.(?:rmtree|copy))\\b|open\\s*\\([^,\\n]+,\\s*['\\\"](?:w|a|x)", re.I),
    "database_destructive": re.compile(r"\\b(?:DROP\\s+TABLE|TRUNCATE\\s+TABLE|DELETE\\s+FROM)\\b", re.I),
    "package_install": re.compile(r"\\b(?:pip\\s+install|npm\\s+install|pnpm\\s+add|yarn\\s+add|uv\\s+add|apt(?:-get)?\\s+install|brew\\s+install)\\b", re.I),
    "remote_tool_or_mcp": re.compile(r"\\b(?:MCP|tool_call|remote\\s+tool)\\b", re.I),
}

def static_flags(text):
    return [name for name, pattern in STATIC_PATTERNS.items() if pattern.search(text)]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--selected-entrypoints",type=Path,required=True)
    ap.add_argument("--primary-manifest",type=Path,required=True)
    ap.add_argument("--motion-manifest",type=Path,required=True)
    ap.add_argument("--motion-manifest-part2",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--workers",type=int,default=8); ap.add_argument("--timeout",type=int,default=40); ap.add_argument("--retries",type=int,default=3)
    a=ap.parse_args()
    selected=read_csv(a.selected_entrypoints); primary=read_csv(a.primary_manifest)
    motion=read_csv(a.motion_manifest)+read_csv(a.motion_manifest_part2)
    index=defaultdict(dict)
    for r in primary:
        if r.get("type")=="blob": index[(r["repository"],r["commit"])][r["path"]]=r
    for r in motion:
        if r.get("type")=="blob":
            repo="iart-ai/"+r["pack"]; index[(repo,r["commit"])][r["path"]]={**r,"source":"Motion Skills"}
    queue={}
    for s in selected:
        key=(s["repository"],s["commit"]); prefix=str(PurePosixPath(s["path"]).parent).rstrip("/")+"/"
        for path,meta in index.get(key,{}).items():
            if path.startswith(prefix): queue[(key[0],key[1],path)]={"source":s["source"],"repository":key[0],"commit":key[1],"path":path,"git_sha":meta.get("git_sha",""),"size":meta.get("size_bytes",""),"entrypoint":s["path"]}
    seen=set(); files=[]; links=[]; static_reviews=[]
    while True:
        batch=[(k,v) for k,v in queue.items() if k not in seen]
        if not batch: break
        seen.update(k for k,_ in batch); fetched={}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,a.workers)) as pool:
            fs={pool.submit(fetch,row["repository"],row["commit"],row["path"],a.timeout,a.retries):key for key,row in batch}
            for f in concurrent.futures.as_completed(fs): fetched[fs[f]]=f.result()
        for key,row in batch:
            raw,status=fetched[key]; kind,disp,reason=classify(row["path"])
            base={"source":row["source"],"repository":row["repository"],"commit":row["commit"],"skill_entrypoint":row["entrypoint"],"path":row["path"],"content_kind":kind,"proposed_disposition":disp,"disposition_status":"PRELIMINARY_NOT_FINAL","git_blob_sha":row["git_sha"],"expected_bytes":row["size"],"review_reason":reason}
            if raw is None:
                files.append({**base,"fetch_status":status,"raw_bytes":"","sha256":"","computed_git_blob_sha":"","git_blob_match":"NOT_VERIFIED","size_match":"NOT_VERIFIED","sha256_status":"FETCH_FAILED"}); continue
            blob=git_blob_sha1(raw); size_ok=not row["size"].isdigit() or len(raw)==int(row["size"]); blob_ok=not row["git_sha"] or blob==row["git_sha"]
            files.append({**base,"fetch_status":"FETCHED","raw_bytes":str(len(raw)),"sha256":hashlib.sha256(raw).hexdigest(),"computed_git_blob_sha":blob,"git_blob_match":"YES" if blob_ok else "NO","size_match":"YES" if size_ok else "NO","sha256_status":"VERIFIED" if blob_ok and size_ok else "REVIEW_REQUIRED"})
            try: text=raw.decode("utf-8")
            except UnicodeDecodeError:
                if kind in {"executable-source","configuration-or-schema"}:
                    static_reviews.append({"repository":row["repository"],"commit":row["commit"],"skill_entrypoint":row["entrypoint"],"path":row["path"],"content_kind":kind,"raw_bytes":len(raw),"scan_status":"NON_UTF8_BINARY","pattern_flags":"","flag_count":0,"risk_tier":"MANUAL_REVIEW","manual_review_required":"YES","note":"Static text scan skipped; binary-safe hash evidence remains separate"})
                continue
            if kind in {"executable-source","configuration-or-schema"}:
                flags=static_flags(text)
                high={"dynamic_code","process_spawn","database_destructive"}
                tier="HIGH_REVIEW" if any(x in high for x in flags) else ("REVIEW" if flags else "NO_PATTERN_FLAG")
                static_reviews.append({"repository":row["repository"],"commit":row["commit"],"skill_entrypoint":row["entrypoint"],"path":row["path"],"content_kind":kind,"raw_bytes":len(raw),"scan_status":"SCANNED_UTF8","pattern_flags":";".join(flags),"flag_count":len(flags),"risk_tier":tier,"manual_review_required":"YES","note":"Pattern flags are triage signals, not vulnerability findings or safety clearance"})
            known=set(index.get((row["repository"],row["commit"]),{}))
            for ref in refs(text,row['path']):
                external=ref.lower().startswith(("http://","https://","mailto:")); resolved=None if external else resolve(row["path"],ref,known)
                links.append({"repository":row["repository"],"commit":row["commit"],"from_path":row["path"],"reference":ref,"resolved_path":resolved or "","status":"EXTERNAL_REFERENCE" if external else ("RESOLVED_IN_PINNED_TREE" if resolved else "NOT_FOUND_IN_PINNED_TREE")})
                if resolved:
                    target=(row["repository"],row["commit"],resolved)
                    if target not in queue:
                        meta=index[(row["repository"],row["commit"])][resolved]
                        queue[target]={"source":row["source"],"repository":row["repository"],"commit":row["commit"],"path":resolved,"git_sha":meta.get("git_sha",""),"size":meta.get("size_bytes",""),"entrypoint":row["entrypoint"]}
    a.out_dir.mkdir(parents=True,exist_ok=True)
    def write(name,rows):
        cols=list(dict.fromkeys(k for r in rows for k in r))
        with (a.out_dir/name).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
    write("skill-payload-file-audit.csv",files); write("skill-reference-audit.csv",links); write("skill-executable-static-review.csv",static_reviews)
    statuses=Counter(x["sha256_status"] for x in files)
    summary={"selected_skill_entrypoints":len(selected),"payload_files":len(files),"sha256_verified":statuses["VERIFIED"],"hash_review_required":statuses["REVIEW_REQUIRED"],"fetch_failed":statuses["FETCH_FAILED"],"content_kinds":dict(Counter(x["content_kind"] for x in files)),"proposed_dispositions":dict(Counter(x["proposed_disposition"] for x in files)),"reference_statuses":dict(Counter(x["status"] for x in links)),"static_review_files":len(static_reviews),"static_review_pattern_flags":dict(Counter(flag for x in static_reviews for flag in x.get("pattern_flags","").split(";") if flag)),"warning":"Hash integrity is not license approval, malware clearance, provider approval or production suitability. No source is executed."}
    (a.out_dir/"skill-payload-audit-summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())
