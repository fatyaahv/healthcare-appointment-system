# Healthcare Appointment System
XML Course Final Project

## Project Roles

- Person 1: XML foundation, XSD validation, XPath queries, invalid XML examples
- Person 2: XSLT transformation, XML parsing, generated XML outputs, error handling
- Person 3: REST API, external service integration, testing, deployment

## XML-Based Appointment Portal

This project uses XML as the main data format. The portal stores patient registrations and live appointment slots in `portal_data.xml`.

### Run

```bash
python api_server.py
```

Open:

```text
http://127.0.0.1:8000/
```

Backend documentation is available directly at:

```text
http://127.0.0.1:8000/docs
```

The XML endpoint document is available at:

```text
http://127.0.0.1:8000/openapi.xml
```

These documentation links are not shown in the frontend navigation.

### Main XML Files

- `appointments.xml`: original XML appointment dataset
- `healthcare.xsd`: XML schema validation file
- `portal_data.xml`: patient registration and doctor-created live appointment slots
- `appointment_report.xsl`: XSLT report transformation
- `report.html`: generated HTML report

### Portal Flow

- The screen has `Kayıt Ol` and `Giriş Yap` options.
- Registration is only for patients.
- Patient registration asks for TC, birth date, first name, and last name.
- TC must be exactly 11 digits.
- Login has role selection: patient or doctor.
- Patient login asks for TC and birth date.
- Doctor login asks for doctor ID and code.
- Doctors create appointment slots after login.
- Doctor-created slots are generated every 15 minutes.
- Patients filter appointments by city, district, hospital, department, doctor, and date.
- Available slots are green.
- Booked slots are red.
- Doctors can see booked patients' first name, last name, and TC.

### Current Location Data

- City: Istanbul
- District: Umraniye
- Hospital: Umraniye Egitim ve Arastirma Hastanesi

Hospitals and departments are dropdown selections, not free-text fields.

### Departments and Doctor Codes

Kardiyoloji:

- D01 Ahmet Yilmaz: 1001
- D02 Elif Kaya: 1002
- D03 Mert Aydin: 1003

Goz Hastaliklari:

- D04 Can Demir: 1004
- D05 Zeynep Sahin: 1005
- D06 Deniz Arslan: 1006

Cocuk Sagligi:

- D07 Murat Celik: 1007
- D08 Selin Yildiz: 1008
- D09 Burak Ozturk: 1009

Ortopedi:

- D10 Hakan Arslan: 1010
- D11 Yasemin Bulut: 1011
- D12 Omer Faruk: 1012

Dermatoloji:

- D13 Merve Acar: 1013
- D14 Kerem Polat: 1014
- D15 Ece Kurt: 1015

### Run Tests

```bash
python -m unittest test_api.py
```
