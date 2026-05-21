from collections import Counter
from pathlib import Path
from xml.sax import ContentHandler, SAXParseException, make_parser


XML_FILE = Path("appointments.xml")


class AppointmentSaxHandler(ContentHandler):
    def __init__(self) -> None:
        super().__init__()
        self.current_element = ""
        self.current_appointment = {}
        self.in_appointment = False
        self.total_appointments = 0
        self.status_counts = Counter()
        self.doctor_counts = Counter()

    def startElement(self, name: str, attrs) -> None:
        self.current_element = name
        if name == "appointment":
            self.in_appointment = True
            self.current_appointment = {}

    def characters(self, content: str) -> None:
        value = content.strip()
        if self.in_appointment and value:
            previous = self.current_appointment.get(self.current_element, "")
            self.current_appointment[self.current_element] = previous + value

    def endElement(self, name: str) -> None:
        if name == "appointment":
            self.total_appointments += 1
            status = self.current_appointment.get("status", "Unknown")
            doctor_id = self.current_appointment.get("doctorId", "Unknown")
            self.status_counts[status] += 1
            self.doctor_counts[doctor_id] += 1
            self.in_appointment = False
            self.current_appointment = {}
        self.current_element = ""


def main() -> None:
    if not XML_FILE.exists():
        print(f"File error: missing XML file: {XML_FILE}")
        return

    parser = make_parser()
    handler = AppointmentSaxHandler()
    parser.setContentHandler(handler)

    try:
        parser.parse(str(XML_FILE))
    except SAXParseException as exc:
        print(f"SAX parse error: line {exc.getLineNumber()}, column {exc.getColumnNumber()}: {exc}")
        return

    print("SAX Parser Report")
    print(f"Total appointments: {handler.total_appointments}")
    print("Status counts:")
    for status, count in sorted(handler.status_counts.items()):
        print(f"  {status}: {count}")

    print("Appointments per doctor:")
    for doctor_id, count in sorted(handler.doctor_counts.items()):
        print(f"  {doctor_id}: {count}")


if __name__ == "__main__":
    main()
