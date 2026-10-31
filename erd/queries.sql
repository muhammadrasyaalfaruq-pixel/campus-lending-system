-- ==========================================================
-- PinjamKampus - UTS Database SQL Queries
-- ==========================================================

-- 1. Query Menampilkan Data Peminjaman Aktif beserta Peminjam dan Barangnya
SELECT 
    l.loan_code AS Kode_Pinjam,
    u.name AS Nama_Peminjam,
    u.student_id AS NIM,
    l.borrow_date AS Tanggal_Pinjam,
    l.due_date AS Batas_Kembali,
    l.status AS Status_Pinjam,
    i.name AS Nama_Barang,
    ld.quantity AS Jumlah
FROM loans l
JOIN users u ON l.user_id = u.id
JOIN loan_details ld ON l.id = ld.loan_id
JOIN items i ON ld.item_id = i.id
WHERE l.status IN ('approved', 'borrowed')
ORDER BY l.borrow_date DESC;

-- 2. Query Pencarian Stok Barang Berdasarkan Kategori
SELECT 
    c.name AS Kategori,
    i.code AS Kode_Barang,
    i.name AS Nama_Barang,
    i.total_stock AS Total,
    i.available_stock AS Tersedia,
    i.condition AS Kondisi
FROM items i
JOIN categories c ON i.category_id = c.id
WHERE i.available_stock > 0
ORDER BY c.name, i.name;

-- 3. Query Rekapitulasi Jumlah Peminjaman per Pengguna (Mahasiswa)
SELECT 
    u.student_id AS NIM,
    u.name AS Nama_Mahasiswa,
    COUNT(l.id) AS Total_Peminjaman
FROM users u
LEFT JOIN loans l ON u.id = l.user_id
WHERE u.role_id = (SELECT id FROM roles WHERE name = 'user')
GROUP BY u.id, u.student_id, u.name
ORDER BY Total_Peminjaman DESC;

-- 4. Query Barang yang Paling Sering Dipinjam
SELECT 
    i.code AS Kode_Barang,
    i.name AS Nama_Barang,
    SUM(ld.quantity) AS Total_Dipinjam
FROM items i
JOIN loan_details ld ON i.id = ld.item_id
GROUP BY i.id, i.code, i.name
ORDER BY Total_Dipinjam DESC
LIMIT 5;

-- 5. Query Laporan Denda dan Status Pembayaran Keterlambatan
SELECT 
    l.loan_code AS Kode_Pinjam,
    u.name AS Peminjam,
    f.days_late AS Hari_Terlambat,
    f.rate_per_day AS Tarif_Per_Hari,
    f.amount AS Total_Denda,
    f.payment_status AS Status_Denda
FROM fines f
JOIN loan_details ld ON f.loan_detail_id = ld.id
JOIN loans l ON ld.loan_id = l.id
JOIN users u ON l.user_id = u.id
ORDER BY f.amount DESC;
