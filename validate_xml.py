import sys

try:
    from lxml import etree
except ImportError:
    print("\nHATA: Bu scripti calistirabilmek icin 'lxml' kütüphanesi gereklidir.")
    print("Kurmak icin terminale sunu yazin: pip install lxml\n")
    sys.exit(1)

def validate_xml(xml_path, xsd_path):
    print(f"--- '{xml_path}' Doğrulanıyor ---")
    try:
        # XSD dosyasını oku ve şemayı hazırla
        with open(xsd_path, 'rb') as f_xsd:
            schema_root = etree.XML(f_xsd.read())
            schema = etree.XMLSchema(schema_root)
        
        # XML dosyasını oku ve parse et
        with open(xml_path, 'rb') as f_xml:
            xml_doc = etree.parse(f_xml)
        
        # Doğrula
        schema.assertValid(xml_doc)
        print(f"SONUÇ: [BAŞARILI] '{xml_path}' şema kurallarına tamamen uygundur.\n")
        return True
        
    except etree.DocumentInvalid as e:
        print(f"SONUÇ: [GEÇERSİZ] '{xml_path}' doğrulanamadı!")
        print("Hata Detayları:")
        for error in e.error_log:
            print(f"  - Satır {error.line}: {error.message}")
        print("\n")
        return False
    except Exception as e:
        print(f"Sistem Hatası: {e}\n")
        return False

if __name__ == "__main__":
    xsd_file = "healthcare.xsd"
    
    # 1. Başarılı doğrulamayı göster
    validate_xml("appointments.xml", xsd_file)
    
    # 2. Hatalı doğrulamayı göster
    validate_xml("invalid_appointment.xml", xsd_file)