import { GoogleGenAI } from '@google/genai';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { message, history } = await req.json();

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    const apiKey = process.env.GEMINI_API_KEY;

    if (apiKey && apiKey !== 'MY_GEMINI_API_KEY') {
      try {
        const ai = new GoogleGenAI({ apiKey });
        const systemInstruction = `Kamu adalah MoreAI Assistant, asisten kecerdasan buatan resmi dari ekosistem MoreAI x IndiHome (oleh Telkom Indonesia).
Bicaralah dalam Bahasa Indonesia yang ramah, profesional, cerdas, dan solutif.
Fokus pada produktivitas, riset, penulisan konten, analisis dokumen, strategi bisnis, dan pemanfaatan koneksi Wi-Fi IndiHome.
Gunakan format markdown yang rapi, jelas, dengan bullet points bila perlu.`;

        const response = await ai.models.generateContent({
          model: 'gemini-2.5-flash',
          contents: [
            {
              role: 'user',
              parts: [{ text: `${systemInstruction}\n\nPertanyaan pengguna: ${message}` }],
            },
          ],
        });

        const reply = response.text || 'Maaf, saya tidak dapat menghasilkan respon saat ini.';
        return NextResponse.json({ reply, source: 'MoreAI Knowledge Base & Gemini AI Engine' });
      } catch (geminiError: unknown) {
        console.error('Gemini API call failed, falling back to local model:', geminiError);
      }
    }

    // Contextual local responses matching the reference UI
    const lower = message.toLowerCase();
    let reply = '';

    if (lower.includes('kopi') || lower.includes('umkm') || lower.includes('marketing')) {
      reply = `Berikut beberapa ide konten & strategi marketing untuk kedai kopi (UMKM):

1. **Tips Menyeduh Kopi di Rumah (Home Brewing Guide)**
   - Buat video reels 30 detik cara seduh V60 dengan biji kopi lokal andalan kedai.
2. **Cerita di Balik Biji Kopi Lokal (Origin Story)**
   - Sorot petani mitra dari Temanggung / Gayo untuk membangun *emotional connection*.
3. **Promo Spesial Akhir Pekan (Weekend Perk)**
   - "Beli 2 Es Kopi Susu Aren Gratis 1 Pastry" khusus pelanggan yang terhubung Wi-Fi IndiHome di kafe Anda.
4. **Interactive Quiz & Loyalty**
   - Kumpulkan feedback rasa favorit lewat QR Code MoreAI.`;
    } else if (lower.includes('wifi') || lower.includes('indihome') || lower.includes('koneksi')) {
      reply = `Koneksi Wi-Fi IndiHome Anda saat ini terpantau **Sangat Stabil (100 Mbps)**. 
Benefit yang aktif:
- **Akses MoreAI Premium Gratis**
- **100.000 Poin AI Credit** per bulan
- Latensi ultra-rendah untuk pemrosesan AI agent dan upload file besar.`;
    } else if (lower.includes('ringkas') || lower.includes('dokumen') || lower.includes('pdf')) {
      reply = `Saya telah memindai inti dokumen Anda:
- **Tujuan Utama**: Peningkatan efisiensi operasional 35% dengan otomatisasi AI.
- **Poin Kunci**: Integrasi modul riset, kalender marketing otomatis, dan analitik real-time.
- **Rekomendasi Tindakan**: Mulai dari otomatisasi caption media sosial dan reporting mingguan.`;
    } else {
      reply = `Halo! Saya siap membantu pekerjaan Anda hari ini dengan MoreAI x IndiHome:
- 💡 **Riset Pasar & Analisis**: Menganalisis tren pasar terkini.
- ✍️ **Pembuatan Konten**: Draft artikel, copy iklan, proposal, dan media sosial.
- 📊 **Olah Data & Insight**: Membaca file spreadsheet dan dokumen kerja.
- 💻 **Bantuan Coding**: Menulis dan memeriksa script Python/TypeScript.

Apa yang ingin kita selesaikan sekarang?`;
    }

    return NextResponse.json({
      reply,
      source: 'MoreAI Knowledge Base',
    });
  } catch (error: unknown) {
    console.error('Error in chat API:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
