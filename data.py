import csv
from jobspy import scrape_jobs
import pandas as pd

# 1. Konfigurasi Tampilan Pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# 2. Daftar Posisi yang Akan Dicari
list_posisi = [
    'Data Analyst',
    'Software Tester',
    'Software Engineer',
    'Digital Marketing',
    'Business Analyst'
]

all_jobs = []

# 3. Proses Scraping (Extract)
for posisi in list_posisi:
    print(f"Mengambil data lowongan pekerjaan untuk posisi: {posisi}...")
    try:
        jobs_temps = scrape_jobs(
            site_name=["Indeed", "Linkedin"],
            search_term=posisi,
            location="Indonesia",
            results_wanted=20,
            country_indeed='Indonesia'
        )
        all_jobs.append(jobs_temps)
    except Exception as e:
        print(f"Gagal mengambil data untuk posisi {posisi}: {e}")

# 4. Pengolahan Data (Transform & Load)
if all_jobs:
    # A. Penggabungan Data Mentah
    jobs = pd.concat(all_jobs, ignore_index=True)
    print(f"\nBerhasil! Total seluruh lowongan terkumpul: {len(jobs)} baris")

    # B. FUNGSI PEMBERSIHAN TEKS & KEBOCORAN BRAND
    def clean_leaked_data(row):
        company = str(row.get('company', '')).strip()
        location = str(row.get('location', '')).strip()
        site = str(row.get('site', '')).strip()
        
        # Kata kunci brand/perusahaan yang mungkin bocor ke kolom lain
        brand_keywords = ['tiktok', 'grab', 'sijitu', 'pt', 'cv', 'corp', 'digital', 'tech','Grab','Traveloka','Monee']
        
        # Pengecekan jika nama perusahaan bocor ke kolom location
        loc_lower = location.lower()
        if any(keyword in loc_lower for keyword in brand_keywords):
            row['company'] = location
            row['location'] = 'Jakarta'  # Set default lokasi aman
            
        return row

    # Terapkan perbaikan kebocoran
    jobs = jobs.apply(clean_leaked_data, axis=1)

    # C. FUNGSI TRANSFORMASI KATEGORI PERAN (ROLE CATEGORY)
    def categorize_role(title):
        title = str(title).lower()
        if 'data' in title:
            return 'Data Analyst'
        elif 'qa' in title or 'test' in title or 'quality assurance' in title:
            return 'Software Tester / QA'
        elif 'software' in title or 'engineer' in title or 'developer' in title:
            return 'Software Engineer'
        elif 'marketing' in title:
            return 'Digital Marketing'
        elif 'business analyst' in title:
            return 'Business Analyst'
        else:
            return 'Other'

    # D. FUNGSI TRANSFORMASI & STANDARISASI KOTA (CITY)
    def clean_location(loc):
        if pd.isna(loc):
            return 'Indonesia'
        loc = str(loc).title()
        if 'Jakarta' in loc:
            return 'Jakarta'
        elif 'Bandung' in loc:
            return 'Bandung'
        elif 'Surabaya' in loc:
            return 'Surabaya'
        elif 'Yogyakarta' in loc or 'Jogja' in loc:
            return 'Yogyakarta'
        elif 'Tangerang' in loc:
            return 'Tangerang'
        elif 'Bekasi' in loc:
            return 'Bekasi'
        else:
            return loc.split(',')[0].strip()

    # E. FUNGSI STANDARISASI NAMA PERUSAHAAN & SITE
    def clean_company_name(comp):
        if pd.isna(comp):
            return 'Unspecified'
        comp_str = str(comp).strip()
        if comp_str.lower() == 'tiktok':
            return 'TikTok'
        return comp_str.title()

    def clean_site_name(st):
        if pd.isna(st):
            return 'Unknown'
        st_lower = str(st).strip().lower()
        if 'linkedin' in st_lower:
            return 'LinkedIn'
        elif 'indeed' in st_lower:
            return 'Indeed'
        return st_lower.title()

    # F. TERAPKAN SELURUH TRANSFORMASI
    jobs['role_category'] = jobs['title'].apply(categorize_role)
    jobs['city'] = jobs['location'].apply(clean_location)
    jobs['company'] = jobs['company'].apply(clean_company_name)
    jobs['site'] = jobs['site'].apply(clean_site_name)

    # G. FILTERING LOKER SAMPAH / TIDAK RELEVAN
    exclude_words = ['tukang', 'bangunan', 'konstruksi', 'sales', 'kurir', 'driver', 'security', 'satpam']
    title_lower = jobs['title'].str.lower().fillna('')
    match_exclude = title_lower.apply(lambda x: any(word in x for word in exclude_words))
    
    # Ambil data yang bukan sampah dan kategorinya sesuai
    df_clean = jobs[~match_exclude & (jobs['role_category'] != 'Other')].copy()

    # H. SELEKSI KOLOM AKHIR & SIMPAN KE CSV
    columns_to_keep = ['title', 'role_category', 'company', 'city', 'site', 'job_url', 'description']
    existing_cols = [col for col in columns_to_keep if col in df_clean.columns]
    
    df_final = df_clean[existing_cols].drop_duplicates().reset_index(drop=True)
    # Pastikan hanya baris yang memiliki URL valid dan format kolom lengkap yang diambil
    df_final = df_final[df_final['job_url'].str.startswith('http', na=False)].copy()
    # --- 2. PERBAIKAN PENTING DI BAGIAN EKSPOR CSV ---
    # Bersihkan karakter enter (\n atau \r) pada seluruh kolom teks
    for col in df_final.select_dtypes(include='object').columns:
        df_final[col] = df_final[col].astype(str).str.replace('\n', ' ').str.replace('\r', '').str.strip()

    # Ekspor ke CSV dengan pengaman quoting
    df_final.to_csv(
        'loker_indonesia_clean.csv', 
        index=False,
        sep=',',                # Gunakan koma sebagai pemisah
        quoting=csv.QUOTE_ALL,   # Membungkus seluruh teks dengan tanda kutip ganda ("")
        encoding='utf-8-sig'     # Memastikan karakter dibaca dengan baik oleh Excel
    )
    
    print("\n" + "="*50)
    print("PROSES ETL SELESAI!")
    print(f"Total data bersih tersimpan: {len(df_final)} baris")
    print("File tersimpan: 'loker_indonesia_clean.csv'")
    print("="*50 + "\n")
    print(df_final.head(10))

else:
    print("Tidak ada data yang berhasil ditarik.")