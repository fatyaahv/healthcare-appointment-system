const summaryFields = document.querySelectorAll("[data-summary]");
const clinicDirectory = document.querySelector("#clinicDirectory");
const appointmentsTable = document.querySelector("#appointmentsTable");
const statusFilter = document.querySelector("#statusFilter");
const doctorFilter = document.querySelector("#doctorFilter");
const applyFilters = document.querySelector("#applyFilters");
const holidaySource = document.querySelector("#holidaySource");
const holidayList = document.querySelector("#holidayList");
const patientRegisterForm = document.querySelector("#patientRegisterForm");
const patientLoginForm = document.querySelector("#patientLoginForm");
const doctorLoginForm = document.querySelector("#doctorLoginForm");
const slotCreateForm = document.querySelector("#slotCreateForm");
const portalMessage = document.querySelector("#portalMessage");
const patientState = document.querySelector("#patientState");
const doctorState = document.querySelector("#doctorState");
const bookingDoctor = document.querySelector("#bookingDoctor");
const bookingDate = document.querySelector("#bookingDate");
const refreshSlots = document.querySelector("#refreshSlots");
const slotGrid = document.querySelector("#slotGrid");
const patientBookings = document.querySelector("#patientBookings");
const doctorBookings = document.querySelector("#doctorBookings");
const doctorLoginSelect = document.querySelector("#doctorLoginSelect");

const state = {
  patient: null,
  patientCredentials: null,
  doctor: null,
  doctorCode: "",
  doctors: [],
};

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function formPayload(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function getJson(url) {
  const response = await fetch(url);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${url}`);
  }
  return data;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${url}`);
  }
  return data;
}

function showMessage(message, tone = "info") {
  portalMessage.textContent = message;
  portalMessage.dataset.tone = tone;
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

function renderDoctorOptions(doctors) {
  const options = doctors
    .map((doctor) => {
      const label = `${doctor.doctorId} - Dr. ${doctor.firstName} ${doctor.lastName} (${doctor.clinicName})`;
      return `<option value="${doctor.doctorId}">${label}</option>`;
    })
    .join("");
  bookingDoctor.innerHTML = options;
  doctorLoginSelect.innerHTML = options;
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

function updateSessionLabels() {
  patientState.textContent = state.patient
    ? `${state.patient.firstName} ${state.patient.lastName} (${state.patient.tc})`
    : "Not logged in";
  doctorState.textContent = state.doctor
    ? `Dr. ${state.doctor.firstName} ${state.doctor.lastName} (${state.doctor.doctorId})`
    : "Not logged in";
}

function slotLabel(slot) {
  return `${slot.date} ${slot.time}`;
}

function renderSlots(slots) {
  if (!slots.length) {
    slotGrid.innerHTML = '<p class="empty-state">No doctor-created slots for this filter.</p>';
    return;
  }

  slotGrid.innerHTML = slots
    .map((slot) => {
      const bookedClass = slot.isBooked ? "booked" : "available";
      const action = slot.isBooked
        ? `<span>${slot.patient ? `${slot.patient.firstName} ${slot.patient.lastName}` : "Booked"}</span>`
        : `<button class="slot-action" data-slot-id="${slot.slotId}" type="button">Book</button>`;
      return `
        <article class="slot-card ${bookedClass}">
          <strong>${slot.time}</strong>
          <span>${slot.doctorName}</span>
          <small>${slot.isBooked ? "Booked" : "Available"}</small>
          ${action}
        </article>
      `;
    })
    .join("");
}

function renderBookingList(target, title, slots, includePatient) {
  if (!slots.length) {
    target.innerHTML = `<p class="empty-state">${title}: no appointments yet.</p>`;
    return;
  }

  target.innerHTML = `
    <h4>${title}</h4>
    <ul>
      ${slots
        .map((slot) => {
          const patient = slot.patient;
          const patientText = patient
            ? `${patient.firstName} ${patient.lastName} - TC: ${patient.tc}`
            : "Patient details unavailable";
          return `
            <li>
              <strong>${slotLabel(slot)}</strong>
              <span>${slot.doctorName}</span>
              ${includePatient ? `<em>${patientText}</em>` : ""}
            </li>
          `;
        })
        .join("")}
    </ul>
  `;
}

async function loadSlots() {
  const params = new URLSearchParams();
  if (bookingDoctor.value) {
    params.set("doctorId", bookingDoctor.value);
  }
  if (bookingDate.value) {
    params.set("date", bookingDate.value);
  }
  const data = await getJson(`/api/slots?${params.toString()}`);
  renderSlots(data.slots);
}

async function loadPatientBookings() {
  if (!state.patientCredentials) {
    patientBookings.innerHTML = "";
    return;
  }
  const params = new URLSearchParams(state.patientCredentials);
  const data = await getJson(`/api/patient/bookings?${params.toString()}`);
  renderBookingList(patientBookings, "My appointments", data.appointments, false);
}

async function loadDoctorBookings() {
  if (!state.doctor || !state.doctorCode) {
    doctorBookings.innerHTML = "";
    return;
  }
  const params = new URLSearchParams({ doctorId: state.doctor.doctorId, code: state.doctorCode });
  const data = await getJson(`/api/doctor/bookings?${params.toString()}`);
  renderBookingList(doctorBookings, "Booked patients", data.appointments, true);
}

patientRegisterForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formPayload(patientRegisterForm);
    const data = await postJson("/api/auth/patient/register", payload);
    state.patient = data.patient;
    state.patientCredentials = { tc: payload.tc, birthDate: payload.birthDate };
    updateSessionLabels();
    await loadPatientBookings();
    showMessage("Patient registered and logged in.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

patientLoginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formPayload(patientLoginForm);
    const data = await postJson("/api/auth/patient/login", payload);
    state.patient = data.patient;
    state.patientCredentials = { tc: payload.tc, birthDate: payload.birthDate };
    updateSessionLabels();
    await loadPatientBookings();
    showMessage("Patient login successful.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

doctorLoginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formPayload(doctorLoginForm);
    const data = await postJson("/api/auth/doctor/login", payload);
    state.doctor = data.doctor;
    state.doctorCode = payload.code;
    updateSessionLabels();
    await loadDoctorBookings();
    showMessage("Doctor login successful.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

slotCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.doctor || !state.doctorCode) {
    showMessage("Doctor login is required before creating slots.", "error");
    return;
  }

  try {
    const payload = {
      ...formPayload(slotCreateForm),
      doctorId: state.doctor.doctorId,
      code: state.doctorCode,
    };
    const data = await postJson("/api/doctor/slots", payload);
    bookingDoctor.value = state.doctor.doctorId;
    bookingDate.value = payload.date;
    await loadSlots();
    showMessage(`${data.slots.length} new 15-minute slots created.`, "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

slotGrid.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-slot-id]");
  if (!button) {
    return;
  }
  if (!state.patientCredentials) {
    showMessage("Patient login is required before booking.", "error");
    return;
  }

  try {
    await postJson("/api/patient/appointments", {
      ...state.patientCredentials,
      slotId: button.dataset.slotId,
    });
    await Promise.all([loadSlots(), loadPatientBookings(), loadDoctorBookings()]);
    showMessage("Appointment booked successfully.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

refreshSlots.addEventListener("click", async () => {
  try {
    await loadSlots();
  } catch (error) {
    showMessage(error.message, "error");
  }
});

applyFilters.addEventListener("click", loadAppointments);
doctorFilter.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    loadAppointments();
  }
});

async function initializePortal() {
  bookingDate.value = todayIso();
  slotCreateForm.elements.date.value = todayIso();
  slotCreateForm.elements.startTime.value = "09:00";
  slotCreateForm.elements.endTime.value = "10:00";

  try {
    const [summary, clinics, holidays, portalDoctors] = await Promise.all([
      getJson("/api/reports/summary"),
      getJson("/api/clinics"),
      getJson("/api/integration/holidays?year=2026&countryCode=TR"),
      getJson("/api/portal/doctors"),
    ]);

    state.doctors = portalDoctors.doctors;
    renderSummary(summary);
    renderClinics(clinics.clinics);
    renderHolidays(holidays);
    renderDoctorOptions(portalDoctors.doctors);
    updateSessionLabels();
    await Promise.all([loadAppointments(), loadSlots()]);
  } catch (error) {
    setText("#holidaySource", "Local API is not available");
    clinicDirectory.innerHTML = '<p class="section-copy">Start the API server to load clinic data.</p>';
    appointmentsTable.innerHTML = '<tr><td colspan="5">Start the API server to load appointment records.</td></tr>';
    slotGrid.innerHTML = '<p class="empty-state">Start the API server to use the portal.</p>';
  }
}

initializePortal();
