const summaryFields = document.querySelectorAll("[data-summary]");
const clinicDirectory = document.querySelector("#clinicDirectory");
const appointmentsTable = document.querySelector("#appointmentsTable");
const statusFilter = document.querySelector("#statusFilter");
const doctorFilter = document.querySelector("#doctorFilter");
const applyFilters = document.querySelector("#applyFilters");
const holidaySource = document.querySelector("#holidaySource");
const holidayList = document.querySelector("#holidayList");

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) {
    node.textContent = value;
  }
}

function renderSummary(summary) {
  summaryFields.forEach((field) => {
    field.textContent = summary[field.dataset.summary] ?? "--";
  });
}

function renderClinics(clinics) {
  clinicDirectory.innerHTML = clinics
    .map(
      (clinic) => `
        <article class="clinic-card">
          <span>${clinic.clinicId}</span>
          <strong>${clinic.clinicName}</strong>
          <ul class="doctor-list">
            ${clinic.doctors
              .map((doctor) => `<li>${doctor.doctorId} - Dr. ${doctor.firstName} ${doctor.lastName}</li>`)
              .join("")}
          </ul>
        </article>
      `,
    )
    .join("");
}

function renderAppointments(appointments) {
  appointmentsTable.innerHTML = appointments
    .slice(0, 10)
    .map((appointment) => {
      const statusClass = appointment.status.toLowerCase();
      const appointmentDate = new Date(appointment.appointmentDateTime).toLocaleString("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
      });
      return `
        <tr>
          <td>${appointment.appointmentId}</td>
          <td>${appointmentDate}</td>
          <td>${appointment.doctorId}</td>
          <td>${appointment.patientId}</td>
          <td><span class="status ${statusClass}">${appointment.status}</span></td>
        </tr>
      `;
    })
    .join("");
}

async function loadAppointments() {
  const params = new URLSearchParams();
  if (statusFilter.value) {
    params.set("status", statusFilter.value);
  }
  if (doctorFilter.value.trim()) {
    params.set("doctorId", doctorFilter.value.trim().toUpperCase());
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  const data = await getJson(`/api/appointments${suffix}`);
  renderAppointments(data.appointments);
}

function renderHolidays(data) {
  holidaySource.textContent = data.source;
  holidayList.innerHTML = data.holidays
    .slice(0, 6)
    .map(
      (holiday) => `
        <li>
          <time datetime="${holiday.date}">${holiday.date}</time>
          <span>${holiday.localName || holiday.name}</span>
        </li>
      `,
    )
    .join("");
}

async function initializePortal() {
  try {
    const [summary, clinics, holidays] = await Promise.all([
      getJson("/api/reports/summary"),
      getJson("/api/clinics"),
      getJson("/api/integration/holidays?year=2026&countryCode=TR"),
    ]);

    renderSummary(summary);
    renderClinics(clinics.clinics);
    renderHolidays(holidays);
    await loadAppointments();
  } catch (error) {
    setText("#holidaySource", "Local API is not available");
    clinicDirectory.innerHTML = '<p class="section-copy">Start the API server to load clinic data.</p>';
    appointmentsTable.innerHTML = '<tr><td colspan="5">Start the API server to load appointment records.</td></tr>';
  }
}

applyFilters.addEventListener("click", loadAppointments);
doctorFilter.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    loadAppointments();
  }
});

initializePortal();
