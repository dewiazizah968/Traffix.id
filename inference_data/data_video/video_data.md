Dokumentasi Data Video CCTV Traffix.id

Alur Pengolahan Data Video

1. Scrapping Video CCTV
Script mengumpulkan link dan video CCTV dari sumber publik Kementerian Pekerjaan Umum Direktorat Jenderal Marga

2. Penyimpanan Video
Video yang sudah dikumpulkan disimpan di Google Drive untuk memudahkan akses dan pengolahan:
https://drive.google.com/drive/folders/1qJQ_B9wZP_kuzXoqaEtjVzBwLJTw3a0g?usp=sharing

3. Inventarisasi Video
Video diorganisir berdasarkan folder (pagi/siang/malam) dan nama file, memastikan tidak ada duplikasi, dan urut sesuai waktu serta lokasi

4. Ekstraksi Frame Otomatis
Frame diambil dari setiap video pada interval 1s, 3s, dan 5s untuk menyiapkan snapshot yang siap dibaca overlay CCTV

5. Pemilihan Frame Terbaik
Frame terbaik dipilih untuk memastikan overlay CCTV terbaca jelas sehingga lokasi KM/GT dapat ditentukan akurat

6. Input Lokasi CCTV
Metadata lokasi diisi berdasarkan overlay yang terbaca. Semua format KM/GT divalidasi agar konsisten

7. Validasi Metadata dan Konversi KM
Metadata video diperiksa dan KM dikonversi ke format numerik yang seragam

8. Pembuatan Daftar Lokasi Unik
Daftar lokasi CCTV unik dibuat dari seluruh video untuk menghilangkan duplikasi dan menyusun koordinat yang valid

9. Pengisian dan Validasi Koordinat Lat-Long
Koordinat GPS setiap lokasi diisi dan divalidasi agar sesuai overlay dan data resmi

10. Pengambilan Data Cuaca Otomatis
Data cuaca diambil untuk setiap lokasi dan waktu video melalui API, menambahkan kolom cuaca ke metadata.

11. Pembuatan Dataset Akhir
Metadata video, koordinat, dan data cuaca digabung menjadi dataset akhir yang siap digunakan untuk inference dan analisis.

Catatan
Folder data_video berisi semua script dan video yang digunakan. Dataset ini sudah siap untuk pipeline inference Traffix.id dan validasi metadata telah dilakukan.