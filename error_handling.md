# Person 2 - Error Handling Notes

This part of the project focuses on parsing, transforming, and generating XML outputs from `appointments.xml`.

## Handled Error Cases

- Missing XML file: parser scripts print a clear file error and stop.
- Invalid XML syntax: DOM and SAX parsers catch parse errors and print the line/column or parser message.
- Optional XSD validation: `parser_dom.py` validates against `schema.xsd` when `lxml` is installed.
- Missing output data: `generate_outputs.py` stops safely if no appointments are found.
- Output folder creation: `generate_outputs.py` creates the `outputs` folder automatically.

## Commands

```bash
python parser_dom.py
python parser_sax.py
python generate_outputs.py
```

To create the HTML report with Python and `lxml`:

```bash
python -c "from lxml import etree; xml=etree.parse('appointments.xml'); xsl=etree.parse('appointment_report.xsl'); open('report.html','wb').write(etree.XSLT(xsl)(xml))"
```
