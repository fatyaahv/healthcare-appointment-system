# Person 3 - Web Services & Integration

## REST API development

The API is implemented in `api_server.py` with Python standard-library modules only. It reads the existing `appointments.xml` dataset and exposes it as JSON.

### Run locally

```bash
python api_server.py
```

Default server URL:

```text
http://127.0.0.1:8000
```

### Main endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | API status check |
| GET | `/api/clinics` | List clinics with doctors |
| GET | `/api/doctors` | List doctors |
| GET | `/api/patients` | List patients |
| GET | `/api/appointments` | List appointments |
| GET | `/api/appointments?status=Pending` | Filter appointments by status |
| GET | `/api/appointments?doctorId=D01` | Filter appointments by doctor |
| GET | `/api/appointments/A01` | Get one appointment |
| GET | `/api/reports/summary` | Appointment totals and status counts |
| GET | `/api/integration/holidays?year=2026&countryCode=TR` | External holiday-service integration |

## Swagger documentation

Swagger UI is available after starting the API:

```text
http://127.0.0.1:8000/docs
```

The raw OpenAPI document is available at:

```text
http://127.0.0.1:8000/openapi.json
```

## External service integration

The `/api/integration/holidays` endpoint calls the public Nager.Date REST API:

```text
https://date.nager.at/api/v3/PublicHolidays/{year}/{countryCode}
```

This demonstrates how the appointment system can connect to an outside service, for example to avoid scheduling on public holidays. If there is no internet connection during a class demo, the code returns an offline Turkey holiday fallback so the endpoint still works.

## Testing

Run the automated tests with:

```bash
python -m unittest test_api.py
```

The tests cover:

- XML-backed appointment listing
- Query filters
- Single appointment lookup
- Error handling for invalid filters and missing appointments
- Summary reporting
- External-service endpoint behavior with a test stub

## Deployment

This project can be deployed anywhere that supports Python 3.10+.

### Simple server deployment

```bash
python api_server.py
```

For a classroom demo, expose port `8000` and open `/docs` for Swagger.

### Docker deployment

Build and run:

```bash
docker build -t healthcare-appointment-api .
docker run -p 8000:8000 healthcare-appointment-api
```

Then open:

```text
http://localhost:8000/docs
```
