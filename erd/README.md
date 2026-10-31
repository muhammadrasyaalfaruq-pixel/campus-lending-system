# ERD (Entity Relationship Diagram) - PinjamKampus

Berikut adalah dokumen relasi antar entitas (ERD) untuk sistem **PinjamKampus** berbasis database MySQL dan model SQLAlchemy di [app/models/entities.py](../app/models/entities.py).

## Diagram Mermaid (Visual Rendereable)

```mermaid
erDiagram
    roles ||--o{ users : "has"
    categories ||--o{ items : "contains"
    users ||--o{ loans : "requests"
    users ||--o{ loans : "approves"
    loans ||--|{ loan_details : "includes"
    items ||--o{ loan_details : "borrowed_in"
    loan_details ||--o| fines : "incurs"
    users ||--o{ notifications : "receives"
    loans ||--o{ notifications : "triggers"

    roles {
        int id PK
        string name
    }

    users {
        int id PK
        int role_id FKs
        string name
        string email
        string password_hash
        string student_id
        string phone
        datetime created_at
    }

    categories {
        int id PK
        string name
        text description
    }

    items {
        int id PK
        int category_id FK
        string code
        string name
        text description
        int total_stock
        int available_stock
        string condition
        string image_path
        datetime created_at
    }

    loans {
        int id PK
        int user_id FK
        int approved_by FK
        string loan_code
        text purpose
        date borrow_date
        date due_date
        string status
        datetime created_at
    }

    loan_details {
        int id PK
        int loan_id FK
        int item_id FK
        int quantity
        int returned_quantity
        string condition_before
        string condition_after
        date return_date
        text return_note
    }

    fines {
        int id PK
        int loan_detail_id FK
        int days_late
        decimal rate_per_day
        decimal amount
        string payment_status
        datetime paid_at
    }

    notifications {
        int id PK
        int user_id FK
        int loan_id FK
        string title
        text message
        boolean is_read
        datetime created_at
    }
```

---

## Format DBML (Untuk dbdiagram.io)

Jika ingin mengeksport ke gambar ERD resolusi tinggi, buka [dbdiagram.io](https://dbdiagram.io) dan tempelkan kode DBML berikut:

```dbml
Table roles {
  id int [pk, increment]
  name varchar
}

Table users {
  id int [pk, increment]
  role_id int [ref: > roles.id]
  name varchar
  email varchar
  password_hash varchar
  student_id varchar
  phone varchar
  created_at datetime
}

Table categories {
  id int [pk, increment]
  name varchar
  description text
}

Table items {
  id int [pk, increment]
  category_id int [ref: > categories.id]
  code varchar
  name varchar
  description text
  total_stock int
  available_stock int
  condition varchar
  image_path varchar
  created_at datetime
}

Table loans {
  id int [pk, increment]
  user_id int [ref: > users.id]
  approved_by int [ref: > users.id]
  loan_code varchar
  purpose text
  borrow_date date
  due_date date
  status varchar
  created_at datetime
}

Table loan_details {
  id int [pk, increment]
  loan_id int [ref: > loans.id]
  item_id int [ref: > items.id]
  quantity int
  returned_quantity int
  condition_before varchar
  condition_after varchar
  return_date date
  return_note text
}

Table fines {
  id int [pk, increment]
  loan_detail_id int [ref: - loan_details.id]
  days_late int
  rate_per_day decimal
  amount decimal
  payment_status varchar
  paid_at datetime
}

Table notifications {
  id int [pk, increment]
  user_id int [ref: > users.id]
  loan_id int [ref: > loans.id]
  title varchar
  message text
  is_read boolean
  created_at datetime
}
```

---

## Ringkasan Kardinalitas Relasi

1. **roles - users (1 : N):** 1 role dapat dimiliki banyak pengguna.
2. **categories - items (1 : N):** 1 kategori memiliki banyak barang inventaris.
3. **users - loans (1 : N):** 1 pengguna dapat mengajukan banyak peminjaman.
4. **users (admin) - loans (1 : N):** 1 admin dapat menyetujui banyak peminjaman.
5. **loans - loan_details (1 : N):** 1 peminjaman dapat berisi beberapa barang.
6. **items - loan_details (1 : N):** 1 barang dapat dipinjam di banyak riwayat peminjaman.
7. **loan_details - fines (1 : 0..1):** 1 detail peminjaman memiliki maksimal 1 catatan denda.
8. **users - notifications (1 : N):** 1 pengguna menerima banyak notifikasi.
