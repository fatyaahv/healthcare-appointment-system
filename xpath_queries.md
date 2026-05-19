# XML Sağlık Randevu Sistemi - XPath Sorgu Raporu

Bu belgede, `appointments.xml` veri seti üzerinde analiz yapmak, filtreleme uygulamak ve istatistiksel sonuçlar üretmek amacıyla hazırlanan 5 adet ileri düzey XPath sorgusu yer almaktadır.

Sistemimizde varsayılan bir isim alanı (Namespace) kullanıldığı için sorguların çalışabilmesi adına elemanların önünde `tns:` (Target Name Space) öneki kullanılmıştır.

---

### Sorgu 1: Belirli bir klinikteki ("Kardiyoloji") doktorların isim ve soyisimlerini seçmek
*   **Açıklama:** Hiyerarşik yapı içerisinde klinik adına göre filtreleme yapıp, o kliniğe bağlı doktorların verilerini çekmek amacıyla yazılmıştır.
*   **Sorgu:**
    ```xpath
    /tns:appointmentSystem/tns:clinics/tns:clinic[tns:clinicName='Kardiyoloji']/tns:doctors/tns:doctor/tns:firstName | /tns:appointmentSystem/tns:clinics/tns:clinic[tns:clinicName='Kardiyoloji']/tns:doctors/tns:doctor/tns:lastName
    ```
*   **Beklenen Çıktı:** 
    ```text
    Ahmet, Yılmaz, Elif, Kaya
    ```

---

### Sorgu 2: Durumu "Pending" (Beklemede) olan randevuların hasta ID'lerini listelemek
*   **Açıklama:** Koşullu filtreleme yaparak belirli durumdaki randevuları tespit etmek ve ilişkisel analizlerde kullanmak üzere tasarlanmıştır.
*   **Sorgu:**
    ```xpath
    /tns:appointmentSystem/tns:appointments/tns:appointment[tns:status='Pending']/tns:patientId
    ```
*   **Beklenen Çıktı:** 
    ```text
    P01, P04, P05, P10, P06, P09, P07, P10, P02, P03, P04, P05, P07, P06, P08, P09, P10, P01, P02, P03
    ```

---

### Sorgu 3: 1990 yılından önce doğmuş olan (yaşı daha büyük olan) hastaları bulmak
*   **Açıklama:** Tarih string'ini parçalayarak (`substring`) ve sayıya dönüştürerek (`number`) matematiksel büyüklük/küçüklük karşılaştırması yapan ileri düzey bir sorgudur.
*   **Sorgu:**
    ```xpath
    /tns:appointmentSystem/tns:patients/tns:patient[number(substring(tns:dateOfBirth, 1, 4)) < 1990]/tns:firstName
    ```
*   **Beklenen Çıktı:** 
    ```text
    Mehmet, Fatma, Mustafa, Yasemin
    ```

---

### Sorgu 4: Açıklama (notes) kısmında "kontrol" veya "Kontrol" kelimesi geçen tüm randevuların tarih ve saatlerini almak
*   **Açıklama:** Metinsel arama fonksiyonunu (`contains`) ve mantıksal operatörleri (`or`) kullanarak dinamik içerik analizi yapar.
*   **Sorgu:**
    ```xpath
    /tns:appointmentSystem/tns:appointments/tns:appointment[contains(tns:notes, 'kontrol') or contains(tns:notes, 'Kontrol')]/tns:appointmentDateTime
    ```
*   **Beklenen Çıktı:** 
    ```text
    2026-06-01T09:00:00, 2026-06-01T11:00:00, 2026-06-02T11:30:00, 2026-06-03T15:00:00, 2026-06-08T11:15:00, 2026-06-08T15:30:00
    ```

---

### Sorgu 5: Doktor "D07" (Hakan Arslan) için sistemde tanımlanmış toplam randevu sayısını hesaplamak
*   **Açıklama:** XPath toplama/sayma fonksiyonlarını (`count`) kullanarak veri kümesi üzerinde istatistiksel bilgi üretir.
*   **Sorgu:**
    ```xpath
    count(/tns:appointmentSystem/tns:appointments/tns:appointment[tns:doctorId='D07'])
    ```
*   **Beklenen Çıktı:** 
    ```text
    6
    ```