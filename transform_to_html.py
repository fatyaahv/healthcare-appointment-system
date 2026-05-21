from pathlib import Path


XML_FILE = Path("appointments.xml")
XSL_FILE = Path("appointment_report.xsl")
HTML_FILE = Path("report.html")


def main() -> None:
    try:
        from lxml import etree
    except ImportError:
        print("Missing dependency: install lxml to run the XSLT transformation.")
        print("Example: pip install lxml")
        return

    try:
        xml_doc = etree.parse(str(XML_FILE))
        xsl_doc = etree.parse(str(XSL_FILE))
        transform = etree.XSLT(xsl_doc)
        html_doc = transform(xml_doc)
    except OSError as exc:
        print(f"File error: {exc}")
        return
    except etree.XMLSyntaxError as exc:
        print(f"XML/XSL parse error: {exc}")
        return
    except etree.XSLTApplyError as exc:
        print(f"XSLT transformation error: {exc}")
        return

    HTML_FILE.write_bytes(etree.tostring(html_doc, pretty_print=True, method="html", encoding="UTF-8"))
    print(f"HTML report generated: {HTML_FILE}")


if __name__ == "__main__":
    main()
