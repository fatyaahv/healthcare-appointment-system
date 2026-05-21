# Person 2 - Transformation and Parsing

Person 2 uses the XML dataset created by Person 1 and adds transformation, parsing, output generation, and error handling.

## Added Files

- `appointment_report.xsl`: XSLT file that transforms `appointments.xml` into an HTML report.
- `transform_to_html.py`: Runs the XSLT transformation and creates `report.html`.
- `parser_dom.py`: DOM-style parser that reads the XML tree, counts appointment statuses, and lists doctor appointment totals.
- `parser_sax.py`: SAX parser that processes appointment elements event by event.
- `generate_outputs.py`: Generates new XML files from the source dataset.
- `error_handling.md`: Documents handled parsing and validation errors.

## Generated Outputs

Running `generate_outputs.py` creates:

- `outputs/appointment_summary.xml`
- `outputs/pending_appointments.xml`
- `outputs/doctor_schedule_D01.xml`

## Run

```bash
python transform_to_html.py
python parser_dom.py
python parser_sax.py
python generate_outputs.py
```

## XSLT Transformation

If `lxml` is installed:

```bash
python -c "from lxml import etree; xml=etree.parse('appointments.xml'); xsl=etree.parse('appointment_report.xsl'); open('report.html','wb').write(etree.XSLT(xsl)(xml))"
```

The generated `report.html` contains summary cards, a clinics/doctors table, and a full appointments table.
