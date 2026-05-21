import sys

try:
    from lxml import etree
except ImportError:
    print("\nHATA: Bu scripti calistirabilmek icin 'lxml' kütüphanesi gereklidir.")
    print("Kurmak icin terminale sunu yazin: pip install lxml\n")
    sys.exit(1)

def run_xpath_queries(xml_path):
    # XML dosyasını oku
    with open(xml_path, 'rb') as f:
        xml_doc = etree.parse(f)
        
    # XML içindeki Namespace (İsim Alanı) haritasını tanımla
    namespaces = {'tns': 'https://www.saglikrandevu.com/schema'}
    
    queries = [
        {
            "no": 1,
            "desc": "Kardiyoloji klinigindeki doktorlarin ad ve soyadlari:",
            "xpath": "/tns:appointmentSystem/tns:clinics/tns:clinic[tns:clinicName='Kardiyoloji']/tns:doctors/tns:doctor/tns:firstName | /tns:appointmentSystem/tns:clinics/tns:clinic[tns:clinicName='Kardiyoloji']/tns:doctors/tns:doctor/tns:lastName"
        },
        {
            "no": 2,
            "desc": "Durumu 'Completed' (Tamamlanmis) olan randevularin hasta ID'leri:",
            "xpath": "/tns:appointmentSystem/tns:appointments/tns:appointment[tns:status='Completed']/tns:patientId"
        },
        {
            "no": 3,
            "desc": "1990 yilindan once dogmus olan hastalarin isimleri:",
            "xpath": "/tns:appointmentSystem/tns:patients/tns:patient[number(substring(tns:dateOfBirth, 1, 4)) < 1990]/tns:firstName"
        },
        {
            "no": 4,
            "desc": "Notlarinda 'takibi' gecen randevularin tarih ve saatleri:",
            "xpath": "/tns:appointmentSystem/tns:appointments/tns:appointment[contains(tns:notes, 'takibi')]/tns:appointmentDateTime"
        },
        {
            "no": 5,
            "desc": "Doktor D01'in toplam randevu sayisi:",
            "xpath": "count(/tns:appointmentSystem/tns:appointments/tns:appointment[tns:doctorId='D01'])"
        }
    ]
    
    print("=== XPATH SORGULARI VE SONUÇLARI ===\n")
    
    for q in queries:
        print(f"Sorgu {q['no']}: {q['desc']}")
        print(f"XPath: {q['xpath']}")
        
        # XPath sorgusunu calistir
        result = xml_doc.xpath(q["xpath"], namespaces=namespaces)
        
        # Sonucu ekrana yazdir
        if isinstance(result, float): # count() fonksiyonu float doner
            print(f"Sonuc: {int(result)}")
        elif len(result) == 0:
            print("Sonuc: Bulunamadi")
        else:
            # Gelen elemanlar etree objesi ise metin iceriklerini al, yoksa dogrudan yazdir
            values = [elem.text if hasattr(elem, 'text') else str(elem) for elem in result]
            print(f"Sonuc: {', '.join(values)}")
            
        print("-" * 50)

if __name__ == "__main__":
    run_xpath_queries("appointments.xml")