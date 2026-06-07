# Deployment Notes

Run the XML-based appointment portal with:

```bash
python api_server.py
```

Open:

```text
http://127.0.0.1:8000/
```

The project stores live portal data in `portal_data.xml`. Patient registration, doctor-created slots, and booked appointments remain XML-based.
