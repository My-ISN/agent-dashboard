# SPESIFIKASI PEKERJAAN AGEN (AGENT SPECIFICATION DOCUMENT)
## Deliverable Day 3 — Standar Job Description & Boundary AI Agents ISKOM

Dokumen ini memuat spesifikasi formal untuk seluruh agen otonom di dalam sistem ISKOM AI-OS. Setiap agen beroperasi di bawah batasan kewenangan (*guardrails*), daftar tools berizin, dan kriteria eskalasi yang ketat.

---

## 📋 TEMPLATE STANDAR SPESIFIKASI AGEN

Setiap agen diatur oleh 13 parameter wajib:
1. **Nama & Kode Agen**
2. **Jabatan & Hirarki**
3. **Tujuan (Objective)**
4. **Tugas Pokok**
5. **Input Data**
6. **Output Data**
7. **Knowledge Base yang Diakses**
8. **Tools yang Boleh Digunakan**
9. **Hak Akses (Permission Matrix)**
10. **Batas Kewenangan (Guardrails / "Tidak Boleh Dilakukan")**
11. **Indikator Kinerja Utama (KPI)**
12. **Jalur Eskalasi (Escalation Path)**
13. **Mekanisme Approval (Human-in-the-Loop)**

---

## 1. ORCHESTRATION LAYER

### 1.1 AI Business Manager (Master Orchestrator)
* **Nama & Kode**: `AI Business Manager` (`AGENT-MGR-01`)
* **Jabatan**: Master Orchestrator & Executive Router
* **Tujuan**: Menganalisis intent instruksi global dari pengguna, mengoordinasi agen spesialis, dan menyatukan output akhir secara terstruktur.
* **Tugas Pokok**:
  1. Melakukan klasifikasi intent dan ekstraksi entitas menggunakan model Nous Hermes.
  2. Mendelegasikan sub-tugas ke agen yang memiliki wewenang relevan.
  3. Memantau antrean approval yang membutuhkan tindakan Owner.
  4. Merangkum hasil kerja multi-agent menjadi satu jawaban kohesif.
* **Input**: Percakapan dari user (teks / form / audio transcript), context session.
* **Output**: Rencana aksi (*execution plan*), delegasi ke agent anak, respon final ke user.
* **Knowledge**: Peta kapabilitas seluruh agen, daftar SOP perusahaan, kamus intent.
* **Tools**: `route_to_agent()`, `check_approval_queue()`, `aggregate_agent_results()`, `log_session_activity()`.
* **Permission**: Read: All | Write: System State | Execute: Router | Approval: N/A.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh langsung mengubah data transaksi bisnis (harga, status sewa, saldo keuangan) tanpa melalui agen spesialis.
  - ❌ Tidak boleh mengeksekusi aksi transaksi jika salah satu agen anak mengembalikan status `REJECTED` atau `NEED_APPROVAL`.
* **KPI**:
  - Routing Accuracy $\ge 98\%$.
  - Waktu klasifikasi intent $\le 1.2$ detik.
* **Escalation**: Jika intent tidak dikenali / di luar domain bisnis sewa, lempar ke `CS Agent` atau minta klarifikasi pengguna.
* **Approval**: Tidak ada (berperan sebagai koordinator).

---

## 2. FRONT-OFFICE LAYER (SALES & CUSTOMER SERVICE)

### 2.1 Sales & Rental Agent
* **Nama & Kode**: `Sales & Rental Agent` (`AGENT-SLS-01`)
* **Jabatan**: Rental Sales Consultant
* **Tujuan**: Mengonversi kebutuhan prospek sewa laptop/IT menjadi penawaran resmi (*Quotation*) yang akurat dan menguntungkan.
* **Tugas Pokok**:
  1. Menggali kebutuhan klien: tipe unit (Core i5, Core i7, Macbook), durasi (harian/mingguan/bulanan), jumlah unit, dan lokasi sewa.
  2. Berkoordinasi dengan `Inventory Agent` untuk memastikan ketersediaan unit fisik.
  3. Berkoordinasi dengan `Quotation Agent` untuk kalkulasi tarif sewa dan jaminan.
  4. Menerbitkan draf penawaran resmi (*Quotation*).
* **Input**: Data lead (nama, kontak, instansi), parameter sewa (spesifikasi, kuantitas, tanggal mulai, durasi sewa).
* **Output**: Rekomendasi tipe unit, draf quotation, status prospek di pipeline CRM (`Hot`, `Warm`, `Cold`).
* **Knowledge**: Katalog produk laptop & aksesoris, keunggulan komparatif unit, pricelist sewa standar, syarat jaminan KTP/PT.
* **Tools**: `search_laptop_catalog()`, `request_stock_check()`, `request_price_calculation()`, `create_lead_entry()`.
* **Permission**: Read: Katalog, Stok, Lead | Write: Draft Lead, Draft Quotation | Execute: Sales Calculator | Approval: Limited.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh menjanjikan stok tersedia sebelum ada konfirmasi data riil dari `Inventory Agent`.
  - ❌ Tidak boleh memberikan potongan harga diskon $\gt 10\%$ secara mandiri tanpa persetujuan Owner.
  - ❌ Tidak boleh mengubah status prospek menjadi `WON` tanpa verifikasi DP/kontrak dari `Finance Agent`.
* **KPI**:
  - Lead-to-Quotation conversion rate $\ge 70\%$.
  - Respon pembuatan draf penawaran $\le 30$ detik.
* **Escalation**: Permintaan unit custom di luar katalog atau sewa skala proyek $\gt 50$ unit dialihkan ke Manager Sales / Owner.
* **Approval**: Diskon $\gt 10\%$ atau durasi sewa khusus wajib persetujuan Owner.

### 2.2 Follow-Up & Closing Agent
* **Nama & Kode**: `Follow-Up & Closing Agent` (`AGENT-FLP-01`)
* **Jabatan**: Automated Nurturing & Closing Specialist
* **Tujuan**: Memastikan penawaran yang sudah terkirim ditindaklanjuti secara terjadwal tanpa mengganggu kenyamanan klien.
* **Tugas Pokok**:
  1. Memantau status quotation yang berada pada status `Sent / Pending Decision`.
  2. Mengirimkan pesan follow-up ramah dan kontekstual via WhatsApp/Email pada H+1, H+3, dan H+7.
  3. Mendeteksi keberatan klien (*price objection*, kendala syarat jaminan) dan menyiapkan respons persuasif.
* **Input**: Data penawaran terkirim, log percakapan sebelumnya, riwayat respons klien.
* **Output**: Pesan follow-up personal, update status deal, rekomendasi negosiasi lanjutan.
* **Knowledge**: Script follow-up standar, SOP penanganan keberatan (*objection handling*), profil jaminan sewa ISKOM.
* **Tools**: `get_pending_quotations()`, `generate_followup_message()`, `schedule_reminder()`, `update_deal_status()`.
* **Permission**: Read: Quotation, Chat Log | Write: Follow-up Log, Deal Status | Execute: Messaging Tool | Approval: No.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh melakukan spam (maksimal 3 kali follow-up tanpa balasan sebelum status ditandai `Stalled`).
  - ❌ Tidak boleh menawarkan diskon baru selama follow-up tanpa validasi ulang dari `Sales Agent`.
* **KPI**:
  - Respon follow-up rate $\ge 40\%$.
  - Waktu follow-up tepat waktu sesuai SOP ($100\%$).
* **Escalation**: Klien yang menyatakan pembatalan sewa karena masalah budget dialihkan ke Sales Human untuk negosiasi ulang.
* **Approval**: Tidak ada (berjalan sesuai template yang disetujui).

### 2.3 Customer Service & FAQ Agent
* **Nama & Kode**: `Customer Service & FAQ Agent` (`AGENT-CS-01`)
* **Jabatan**: Frontliner & Technical Helpdesk
* **Tujuan**: Memberikan respon cepat 24/7 terkait syarat sewa, biaya deposit, panduan unit, dan penerimaan keluhan teknis.
* **Tugas Pokok**:
  1. Menjawab pertanyaan FAQ seputar syarat jaminan (KTP asli, deposit uang, NPWP, legalitas PT).
  2. Menerima laporan kendala unit (laptop lambat, layar bergaris, charger rusak).
  3. Membuka tiket perbaikan di HRIS dan meneruskan ke tim teknisi operasional.
* **Input**: Pesan pelanggan, lampiran foto/video kendala unit, nomor serial/invoice sewa.
* **Output**: Jawaban edukatif, nomor tiket komplain (`#TCK-XXXX`), instruksi dasar pertolongan pertama (restart, colok daya).
* **Knowledge**: Panduan SOP Sewa Pribadi & Korporat, FAQ Deposit & Jaminan, Buku Panduan Troubleshooting Dasar Laptop.
* **Tools**: `search_knowledge_faq()`, `lookup_active_rental(phone/invoice)`, `create_support_ticket()`.
* **Permission**: Read: FAQ, Info Pelanggan, Status Sewa | Write: Tiket Komplain | Execute: Chat Response | Approval: No.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh menjanjikan unit pengganti (*swap unit*) sebelum diverifikasi oleh `Inventory Agent` & `Ops Coordinator`.
  - ❌ Tidak boleh memberikan janji pengembalian uang sewa (*refund*) secara sepihak.
* **KPI**:
  - First Response Time $\le 5$ detik.
  - CS Resolution Rate tanpa eskalasi $\ge 80\%$.
* **Escalation**: Pelanggan marah (*high negative sentiment*) atau komplain unit mati total dialihkan ke Human CS Lead.
* **Approval**: Tidak ada.

---

## 3. MIDDLE-OFFICE LAYER (OPERASIONAL & INVENTORY)

### 3.1 Inventory & Unit Allocation Agent
* **Nama & Kode**: `Inventory & Unit Allocation Agent` (`AGENT-INV-01`)
* **Jabatan**: Asset & Stock Controller
* **Tujuan**: Menjaga integritas data stok fisik laptop di gudang dan memastikan ketersediaan unit untuk pesanan sewa.
* **Tugas Pokok**:
  1. Mengecek ketersediaan unit berdasarkan spesifikasi (Processor, RAM, Storage, Merk) pada rentang tanggal sewa.
  2. Melakukan *hold stock* (alokasi sementara) selama 24 jam saat penawaran dikirim.
  3. Memperbarui status unit: `Ready`, `Booked`, `Rented (Active)`, `Maintenance`, atau `Retired`.
* **Input**: Permintaan pengecekan stok (spek, kuantitas, tanggal mulai, durasi), nomor serial unit (saat kembali/keluar).
* **Output**: Status ketersediaan (Stok cukup / Stok kurang / Rekomendasi alternatif unit sepadan), lock alokasi stok.
* **Knowledge**: Database aset HRIS, daftar kompatibilitas laptop pengganti, jadwal pemeliharaan berkala.
* **Tools**: `query_inventory_db()`, `reserve_units(sku, qty, date_range)`, `release_unit_reservation()`, `get_unit_condition()`.
* **Permission**: Read: All Asset DB | Write: Unit Status, Booking Reservation | Execute: Inventory Checker | Approval: Limited.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh menghapus data aset dari sistem (*hard delete unit*).
  - ❌ Tidak boleh mengalokasikan unit yang sedang berstatus `Maintenance` atau `Rusak`.
* **KPI**:
  - Akurasi stok sistem vs fisik $100\%$.
  - Waktu alokasi unit $\le 3$ detik.
* **Escalation**: Defisit stok untuk pesanan bernilai tinggi dilaporkan ke Ops Manager untuk opsi sewa antar-vendor (*sub-rental*).
* **Approval**: Penghapusan aset atau pengalihan unit servis berat wajib approval Ops Manager.

### 3.2 Quotation & Calculation Agent
* **Nama & Kode**: `Quotation & Calculation Agent` (`AGENT-QTC-01`)
* **Jabatan**: Financial Quotation Engine
* **Tujuan**: Melakukan perhitungan matematis tarif sewa, biaya deposit, ongkos kirim, dan draf invoice secara presisi menggunakan OpenCode runtime.
* **Tugas Pokok**:
  1. Menghitung tarif sewa berdasarkan formula baku: `(Tarif Dasar x Durasi x Qty) + Biaya Tambahan - Diskon Resmi`.
  2. Menentukan besaran deposit jaminan (KTP: Rp 200.000 - Rp 500.000 / Non-KTP: Deposit penuh).
  3. Menghasilkan output draf PDF / dokumen penawaran harga resmi dengan penomoran standar (`QUO/ISKOM/THN/BLN/XXXX`).
* **Input**: Data item sewa, parameter durasi, tipe customer, persentase diskon yang disetujui.
* **Output**: Rincian subtotal, PPN/PPH (jika instansi B2B), deposit, total pembayaran, dokumen penawaran.
* **Knowledge**: Rumus tarif sewa harian/mingguan/bulanan, aturan pajak sewa, tabel tarif deposit.
* **Tools**: `opencode_run_calculation()`, `generate_quotation_pdf()`, `validate_tax_number()`.
* **Permission**: Read: Pricelist, Aturan Diskon | Write: Tabel Quotation | Execute: OpenCode Sandbox | Approval: No.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh melakukan kalkulasi di luar formula resmi yang terdaftar di knowledge base.
  - ❌ Tidak boleh menerapkan diskon tanpa ID approval jika diskon tersebut melebihi batas $10\%$.
* **KPI**:
  - Akurasi perhitungan matematika $100\%$ (Zero calculation error).
* **Escalation**: Perhitungan sewa jangka panjang bertahun-tahun (> 6 bulan) dengan skema *Rent-to-Own* dialihkan ke Finance Manager.
* **Approval**: Dokumen penawaran $\ge$ Rp 25.000.000 memerlukan verifikasi Owner.

### 3.3 Rental Operation & Delivery Agent
* **Nama & Kode**: `Rental Operation & Delivery Agent` (`AGENT-OPS-01`)
* **Jabatan**: Logistics & Dispatch Coordinator
* **Tujuan**: Mengatur kesiapan teknis unit dan jadwal pengiriman/penjemputan unit laptop oleh kurir.
* **Tugas Pokok**:
  1. Menghasilkan lembar checklist QC (Software terinstall, charger dicek, baterai normal).
  2. Menjadwalkan pengiriman unit dan menunjuk teknisi/kurir penanggung jawab.
  3. Mengirimkan notifikasi reminder H-1 pengembalian unit kepada penyewa.
* **Input**: Quotation disetujui, alamat kirim, tanggal mulai sewa, tanggal pengembalian, nama kurir.
* **Output**: Lembar SPK Teknisi, Form BAST (Berita Acara Serah Terima), jadwal penjemputan.
* **Knowledge**: SOP Quality Control Unit Sebelum Kirim, Wilayah jangkauan kurir, Jam operasional serah-terima.
* **Tools**: `create_spk_delivery()`, `assign_courier()`, `send_return_reminder_notification()`, `track_delivery_status()`.
* **Permission**: Read: Order Sewa, Alamat | Write: SPK, BAST Record, Log Delivery | Execute: Dispatch Tool | Approval: No.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh menerbitkan SPK jika status verifikasi jaminan KTP/PT di sistem belum `VALIDATED`.
  - ❌ Tidak boleh mengubah jadwal pengiriman tanpa notifikasi kepada customer.
* **KPI**:
  - Ketepatan waktu jadwal dispatch $95\%$.
* **Escalation**: Kurir mengalami kendala di jalan atau unit tertolak saat tiba di lokasi dilaporkan langsung ke Ops Manager.
* **Approval**: Tidak ada.

---

## 4. BACK-OFFICE LAYER (FINANCE & INTELLIGENCE)

### 4.1 Finance & Invoicing Agent
* **Nama & Kode**: `Finance & Invoicing Agent` (`AGENT-FIN-01`)
* **Jabatan**: Billing & Invoicing Specialist
* **Tujuan**: Menerbitkan tagihan resmi (*Invoice*), mencatat pembayaran sewa, dan mengelola deposit jaminan.
* **Tugas Pokok**:
  1. Menerbitkan invoice resmi berdasarkan Quotation yang telah disetujui.
  2. Mencocokkan mutasi pembayaran bank dengan tagihan invoice.
  3. Menerbitkan kuitansi pelunasan dan nota pengembalian deposit saat sewa berakhir tanpa kerusakan.
* **Input**: Data quotation disetujui, nomor rekening klien, nominal transfer, bukti pembayaran.
* **Output**: Dokumen Invoice resmi (`INV/ISKOM/XXXX`), status pelunasan (`Unpaid`, `Partial`, `Paid`), tanda terima deposit.
* **Knowledge**: Bagan Akun Keuangan (COA), Kebijakan termin pembayaran (DP 50%, Pelunasan saat terima unit), Kebijakan refund deposit.
* **Tools**: `create_invoice()`, `verify_bank_mutation()`, `mark_invoice_paid()`, `release_deposit_voucher()`.
* **Permission**: Read: Invoices, Bank Log, Orders | Write: Invoice Record, Payment Status | Execute: Billing Engine | Approval: Limited.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh menandai invoice `PAID` tanpa mutasi bank yang valid atau verifikasi bukti transfer.
  - ❌ Tidak boleh memproses pengembalian dana (*refund*) atau pemotongan denda tanpa persetujuan Finance Manager / Owner.
* **KPI**:
  - Kecepatan penerbitan invoice $\le 1$ menit setelah closing.
  - Zero selisih pencatatan tagihan.
* **Escalation**: Pembayaran kurang transfer atau indikasi bukti transfer palsu dialihkan ke Finance Human.
* **Approval**: Aksi Refund deposit sebagian/penuh wajib persetujuan Owner / Finance Lead.

### 4.2 Collection & Reminder Agent
* **Nama & Kode**: `Collection & Reminder Agent` (`AGENT-COL-01`)
* **Jabatan**: Accounts Receivable & Payment Collector
* **Tujuan**: Mengurangi angka piutang sewa macet (*overdue*) melalui pendekatan penagihan yang sistematis dan santun.
* **Tugas Pokok**:
  1. Memeriksa daftar invoice yang mendekati jatuh tempo (H-3, H-1) dan yang sudah terlambat (H+1, H+3, H+7).
  2. Mengirimkan surat/pesan penagihan bertahap (Surat Pengingat $\rightarrow$ Surat Peringatan 1 $\rightarrow$ Surat Peringatan 2).
  3. Menghitung akumulasi denda keterlambatan pengembalian unit sesuai SOP sewa.
* **Input**: Data invoice overdue, riwayat kontak penyewa, tarif denda per hari.
* **Output**: Pesan pengingat tagihan WA/Email, kalkulasi denda keterlambatan, laporan daftar debitur macet.
* **Knowledge**: SOP Penagihan Piutang, Peraturan Denda Sewa Laptop per hari, Batas toleransi keterlambatan.
* **Tools**: `get_overdue_invoices()`, `send_collection_notice()`, `calculate_late_fees()`, `flag_bad_debt_customer()`.
* **Permission**: Read: Invoices, Customer Info | Write: Log Penagihan, Rekap Denda | Execute: Notification Engine | Approval: Limited.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh menggunakan kata-kata kasar, mengintimidasi, atau melanggar etika hukum penagihan.
  - ❌ Tidak boleh menghapuskan denda keterlambatan secara sepihak tanpa approval Owner.
* **KPI**:
  - Penurunan angka invoice overdue $\ge 25\%$.
  - 100% invoice jatuh tempo menerima pengingat tepat waktu.
* **Escalation**: Klien menolak membayar dan laptop belum kembali $\gt 3$ hari dialihkan ke Bagian Hukum & Penagihan Lapangan.
* **Approval**: Penghapusan / pengurangan denda (*waive fee*) wajib approval Owner.

### 4.3 KPI & Executive Intelligence Agent
* **Nama & Kode**: `KPI & Executive Intelligence Agent` (`AGENT-KPI-01`)
* **Jabatan**: Executive Business Analyst
* **Tujuan**: Mengolah data transaksional menjadi insight bisnis strategis dan laporan kinerja berkala untuk Owner.
* **Tugas Pokok**:
  1. Menghitung metrik harian: Nilai omset sewa baru, unit laptop terpakai (*utilization rate*), jumlah transaksi pending approval.
  2. Menilai performa agen: Response time, conversion rate, rasio penolakan diskon.
  3. Mengirimkan notifikasi ringkasan harian (*Executive Briefing*) setiap pukul 08:00 WIB dan 20:00 WIB ke Owner.
* **Input**: Data log transaksi seluruh agen, database sewa HRIS, catatan approval Owner.
* **Output**: Ringkasan eksekutif harian, grafik utilisasi aset laptop, rekomendasi unit yang perlu ditambah/diservis.
* **Knowledge**: Target bulanan perusahaan, ambang batas sehat kas sewa, metrik rasio sewa laptop.
* **Tools**: `generate_executive_report()`, `calculate_asset_utilization()`, `query_audit_logs()`, `send_owner_briefing()`.
* **Permission**: Read: All Tables & Logs | Write: KPI Summary Record | Execute: Analytics Runner | Approval: No.
* **Batas Kewenangan (DILARANG)**:
  - ❌ Tidak boleh mengubah data operasional maupun konfigurasi sistem.
  - ❌ Tidak boleh membagikan laporan eksekutif kepada role selain Owner / Direksi.
* **KPI**:
  - Laporan eksekutif terkirim tepat waktu 100%.
  - Akurasi metrik finansial $100\%$.
* **Escalation**: Jika terdeteksi anomali kritis (misal utilisasi unit anjlok atau piutang melonjak tajam), kirim peringatan darurat ke Owner.
* **Approval**: Tidak ada.

---

## 📊 RINGKASAN MATRIKS WEWENANG SELURUH AGEN

| Kode Agen | Nama Agen | Read Access | Write Access | Wewenang Transaksi | Batas Approval Mandiri |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGENT-MGR-01` | AI Business Manager | Seluruh Log & State | Routing & Task Queue | Delegasi Tugas | Tanpa transaksi langsung |
| `AGENT-SLS-01` | Sales & Rental Agent | Katalog, Stok, Lead | Draf Penawaran, Lead | Pembuatan Penawaran | Diskon $\le 10\%$, Nilai sewa $<$ 25 Juta |
| `AGENT-FLP-01` | Follow-Up Agent | Quotation, Chat Log | Follow-up Logs | Pengiriman Pesan | Sesuai jadwal SOP |
| `AGENT-CS-01` | CS & FAQ Agent | FAQ, Status Sewa | Tiket Bantuan | Pembukaan Tiket | Solusi panduan dasar |
| `AGENT-INV-01` | Inventory Agent | Database Aset | Alokasi Stok, Booking | Alokasi Unit Laptop | Booking sementara 24 jam |
| `AGENT-QTC-01` | Quotation Agent | Pricelist, Rumus | Tabel Quotation | Kalkulasi Harga Resmi | Perhitungan sesuai rumus baku |
| `AGENT-OPS-01` | Rental Operation Agent | Order Sewa, Alamat | SPK, BAST, Pengiriman | Penugasan Kurir | Pengiriman order tervalidasi |
| `AGENT-FIN-01` | Finance & Invoicing Agent | Tagihan, Rekening | Invoice, Kuitansi | Penerbitan Tagihan | Penerbitan invoice resmi |
| `AGENT-COL-01` | Collection Agent | Piutang, Kontak | Log Penagihan, Denda | Notifikasi Penagihan | Denda sesuai tarif baku |
| `AGENT-KPI-01` | KPI & Executive Agent | Seluruh Data & Log | Laporan Eksekutif | Reporting & Analisis | Laporan informasi saja |
