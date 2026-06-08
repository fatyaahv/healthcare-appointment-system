const summaryFields = document.querySelectorAll("[data-summary]");
const clinicDirectory = document.querySelector("#clinicDirectory");
const publicBookingsTable = document.querySelector("#publicBookingsTable");
const publicBookingsPagination = document.querySelector("#publicBookingsPagination");
const appointmentsTable = document.querySelector("#appointmentsTable");
const statusFilter = document.querySelector("#statusFilter");
const doctorFilter = document.querySelector("#doctorFilter");
const applyFilters = document.querySelector("#applyFilters");
const holidaySource = document.querySelector("#holidaySource");
const holidayList = document.querySelector("#holidayList");
const patientRegisterForm = document.querySelector("#patientRegisterForm");
const patientLoginForm = document.querySelector("#patientLoginForm");
const doctorLoginForm = document.querySelector("#doctorLoginForm");
const masterLoginForm = document.querySelector("#masterLoginForm");
const doctorCreateForm = document.querySelector("#doctorCreateForm");
const slotCreateForm = document.querySelector("#slotCreateForm");
const portalMessage = document.querySelector("#portalMessage");
const patientState = document.querySelector("#patientState");
const doctorState = document.querySelector("#doctorState");
const bookingCity = document.querySelector("#bookingCity");
const bookingDistrict = document.querySelector("#bookingDistrict");
const bookingHospital = document.querySelector("#bookingHospital");
const bookingDepartment = document.querySelector("#bookingDepartment");
const bookingDoctor = document.querySelector("#bookingDoctor");
const bookingDate = document.querySelector("#bookingDate");
const refreshSlots = document.querySelector("#refreshSlots");
const slotGrid = document.querySelector("#slotGrid");
const patientBookings = document.querySelector("#patientBookings");
const doctorBookings = document.querySelector("#doctorBookings");
const doctorLoginSelect = document.querySelector("#doctorLoginSelect");
const loginRole = document.querySelector("#loginRole");
const patientLoginBlock = document.querySelector("#patientLoginBlock");
const doctorLoginBlock = document.querySelector("#doctorLoginBlock");
const masterLoginBlock = document.querySelector("#masterLoginBlock");
const masterDepartment = document.querySelector("#masterDepartment");
const masterHospital = document.querySelector("#masterHospital");
const masterDoctorList = document.querySelector("#masterDoctorList");
const views = {
  home: document.querySelector("#homeView"),
  register: document.querySelector("#registerView"),
  login: document.querySelector("#loginView"),
  patient: document.querySelector("#patientView"),
  doctor: document.querySelector("#doctorView"),
  master: document.querySelector("#masterView"),
};
const patientPanelState = document.querySelector("#patientPanelState");
const doctorPanelState = document.querySelector("#doctorPanelState");
const masterPanelState = document.querySelector("#masterPanelState");

const DEFAULT_CATALOG = {
  cities: [
    {
      cityId: "IST",
      cityName: "Istanbul",
      districts: [
        {
          districtId: "UMR",
          districtName: "Umraniye",
          hospitals: [{ hospitalId: "H01", hospitalName: "Umraniye Egitim ve Arastirma Hastanesi" }],
        },
      ],
    },
  ],
  departments: [
    { departmentId: "CARD", departmentName: "Kardiyoloji" },
    { departmentId: "EYE", departmentName: "Goz Hastaliklari" },
    { departmentId: "PED", departmentName: "Cocuk Sagligi" },
    { departmentId: "ORT", departmentName: "Ortopedi" },
    { departmentId: "DERM", departmentName: "Dermatoloji" },
  ],
};

const DEFAULT_DOCTORS = [
  ["D01", "Ahmet", "Yilmaz", "CARD", "1001"],
  ["D02", "Elif", "Kaya", "CARD", "1002"],
  ["D03", "Mert", "Aydin", "CARD", "1003"],
  ["D04", "Can", "Demir", "EYE", "1004"],
  ["D05", "Zeynep", "Sahin", "EYE", "1005"],
  ["D06", "Deniz", "Arslan", "EYE", "1006"],
  ["D07", "Murat", "Celik", "PED", "1007"],
  ["D08", "Selin", "Yildiz", "PED", "1008"],
  ["D09", "Burak", "Ozturk", "PED", "1009"],
  ["D10", "Hakan", "Arslan", "ORT", "1010"],
  ["D11", "Yasemin", "Bulut", "ORT", "1011"],
  ["D12", "Omer", "Faruk", "ORT", "1012"],
  ["D13", "Merve", "Acar", "DERM", "1013"],
  ["D14", "Kerem", "Polat", "DERM", "1014"],
  ["D15", "Ece", "Kurt", "DERM", "1015"],
].map(([doctorId, firstName, lastName, departmentId, loginCode]) => {
  const department = DEFAULT_CATALOG.departments.find((item) => item.departmentId === departmentId);
  const city = DEFAULT_CATALOG.cities[0];
  const district = city.districts[0];
  const hospital = district.hospitals[0];
  return {
    doctorId,
    firstName,
    lastName,
    loginCode,
    departmentId,
    departmentName: department.departmentName,
    cityId: city.cityId,
    cityName: city.cityName,
    districtId: district.districtId,
    districtName: district.districtName,
    hospitalId: hospital.hospitalId,
    hospitalName: hospital.hospitalName,
  };
});

const state = {
  patient: null,
  patientCredentials: null,
  doctor: null,
  doctorCode: "",
  master: null,
  masterCredentials: null,
  catalog: DEFAULT_CATALOG,
  doctors: DEFAULT_DOCTORS,
  publicBookings: [],
  publicBookingPage: 1,
};

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function formPayload(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function text(node, selector) {
  return node?.querySelector(selector)?.textContent?.trim() || "";
}

function boolText(node, selector) {
  return text(node, selector) === "true";
}

function patientFromNode(node) {
  if (!node) return null;
  return {
    tc: text(node, "tc"),
    birthDate: text(node, "birthDate"),
    firstName: text(node, "firstName"),
    lastName: text(node, "lastName"),
  };
}

function doctorFromNode(node) {
  return {
    doctorId: text(node, "doctorId"),
    firstName: text(node, "firstName"),
    lastName: text(node, "lastName"),
    loginCode: text(node, "loginCode"),
    cityId: text(node, "cityId"),
    cityName: text(node, "cityName"),
    districtId: text(node, "districtId"),
    districtName: text(node, "districtName"),
    hospitalId: text(node, "hospitalId"),
    hospitalName: text(node, "hospitalName"),
    departmentId: text(node, "departmentId"),
    departmentName: text(node, "departmentName"),
  };
}

function slotFromNode(node) {
  return {
    slotId: text(node, "slotId"),
    doctorId: text(node, "doctorId"),
    cityId: text(node, "cityId"),
    cityName: text(node, "cityName"),
    districtId: text(node, "districtId"),
    districtName: text(node, "districtName"),
    hospitalId: text(node, "hospitalId"),
    hospitalName: text(node, "hospitalName"),
    departmentId: text(node, "departmentId"),
    departmentName: text(node, "departmentName"),
    date: text(node, "date"),
    time: text(node, "time"),
    durationMinutes: Number(text(node, "durationMinutes") || "15"),
    isBooked: boolText(node, "isBooked"),
    patientTc: text(node, "patientTc"),
    doctorName: text(node, "doctorName"),
    patient: patientFromNode(node.querySelector("patient")),
  };
}

function publicBookingFromNode(node) {
  const patientPublic = node.querySelector("patientPublic");
  return {
    slotId: text(node, "slotId"),
    date: text(node, "date"),
    time: text(node, "time"),
    doctorName: text(node, "doctorName"),
    departmentName: text(node, "departmentName"),
    hospitalName: text(node, "hospitalName"),
    firstNamePrefix: text(patientPublic, "firstNamePrefix"),
    lastNamePrefix: text(patientPublic, "lastNamePrefix"),
    tcMaskedHash: text(patientPublic, "tcMaskedHash"),
  };
}

function appointmentFromNode(node) {
  return {
    appointmentId: text(node, "appointmentId"),
    doctorId: text(node, "doctorId"),
    patientId: text(node, "patientId"),
    appointmentDateTime: text(node, "appointmentDateTime"),
    status: text(node, "status"),
  };
}

function catalogFromXml(xml) {
  const cityNodes = [...xml.querySelectorAll("cities > city, cities > citie")];
  const cities = cityNodes.map((city) => ({
    cityId: text(city, "cityId"),
    cityName: text(city, "cityName"),
    districts: [...city.querySelectorAll("districts > district")].map((district) => ({
      districtId: text(district, "districtId"),
      districtName: text(district, "districtName"),
      hospitals: [...district.querySelectorAll("hospitals > hospital")].map((hospital) => ({
        hospitalId: text(hospital, "hospitalId"),
        hospitalName: text(hospital, "hospitalName"),
      })),
    })),
  }));
  const departments = [...xml.querySelectorAll("departments > department")].map((department) => ({
    departmentId: text(department, "departmentId"),
    departmentName: text(department, "departmentName"),
  }));
  return { cities, departments };
}

async function getXml(url) {
  const response = await fetch(url);
  const body = await response.text();
  const xml = new DOMParser().parseFromString(body, "application/xml");
  if (!response.ok) {
    throw new Error(text(xml, "error") || `Request failed: ${url}`);
  }
  return xml;
}

async function postForm(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(payload).toString(),
  });
  const body = await response.text();
  const xml = new DOMParser().parseFromString(body, "application/xml");
  if (!response.ok) {
    throw new Error(text(xml, "error") || `Request failed: ${url}`);
  }
  return xml;
}

async function deleteForm(url, payload) {
  const response = await fetch(url, {
    method: "DELETE",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(payload).toString(),
  });
  const body = await response.text();
  const xml = new DOMParser().parseFromString(body, "application/xml");
  if (!response.ok) {
    throw new Error(text(xml, "error") || `Request failed: ${url}`);
  }
  return xml;
}

function showMessage(message, tone = "info") {
  portalMessage.textContent = message;
  portalMessage.dataset.tone = tone;
}

function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) node.textContent = value;
}

function showView(name) {
  Object.entries(views).forEach(([viewName, node]) => {
    const active = viewName === name;
    node.hidden = !active;
    node.classList.toggle("active", active);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function toggleAuthView() {
  const role = loginRole.value;
  patientLoginBlock.hidden = role !== "patient";
  doctorLoginBlock.hidden = role !== "doctor";
  masterLoginBlock.hidden = role !== "master";
}

function renderSummary(xml) {
  summaryFields.forEach((field) => {
    field.textContent = text(xml, field.dataset.summary) || "--";
  });
}

function renderClinics() {
  const departments = [...new Set(state.doctors.map((doctor) => doctor.departmentName))];
  if (!departments.length) {
    clinicDirectory.innerHTML = '<p class="empty-state">Doktor listesi yuklenemedi. API server calisiyor mu kontrol edin.</p>';
    return;
  }
  clinicDirectory.innerHTML = departments
    .map((departmentName) => {
      const doctors = state.doctors.filter((doctor) => doctor.departmentName === departmentName);
      return `
        <article class="clinic-card">
          <span>${doctors[0].hospitalName}</span>
          <strong>${departmentName}</strong>
          <ul class="doctor-list">
            ${doctors
              .map((doctor) => `<li>${doctor.doctorId} - Dr. ${doctor.firstName} ${doctor.lastName} <small>Code: ${doctor.loginCode}</small></li>`)
              .join("")}
          </ul>
        </article>
      `;
    })
    .join("");
}

function formatSlotDate(slot) {
  if (!slot.date || !slot.time) return "--";
  return new Date(`${slot.date}T${slot.time}:00`).toLocaleString("tr-TR", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function renderPublicBookings() {
  const pageSize = 10;
  const totalPages = Math.max(1, Math.ceil(state.publicBookings.length / pageSize));
  state.publicBookingPage = Math.min(Math.max(1, state.publicBookingPage), totalPages);
  const start = (state.publicBookingPage - 1) * pageSize;
  const pageItems = state.publicBookings.slice(start, start + pageSize);

  if (!pageItems.length) {
    publicBookingsTable.innerHTML = '<tr><td colspan="6">Henuz alinan randevu yok.</td></tr>';
    publicBookingsPagination.innerHTML = "";
    return;
  }

  publicBookingsTable.innerHTML = pageItems
    .map((booking) => `
      <tr>
        <td>${formatSlotDate(booking)}</td>
        <td>${booking.firstNamePrefix}** ${booking.lastNamePrefix}**</td>
        <td>${booking.tcMaskedHash}</td>
        <td>${booking.doctorName}</td>
        <td>${booking.departmentName}</td>
        <td>${booking.hospitalName}</td>
      </tr>
    `)
    .join("");

  publicBookingsPagination.innerHTML = Array.from({ length: totalPages }, (_, index) => {
    const page = index + 1;
    const active = page === state.publicBookingPage ? "active" : "";
    return `<button class="${active}" type="button" data-public-page="${page}">${page}</button>`;
  }).join("");
}

async function loadPublicBookings() {
  const xml = await getXml("/api/public/bookings");
  state.publicBookings = [...xml.querySelectorAll("appointments > appointment")].map(publicBookingFromNode);
  renderPublicBookings();
}

function options(items, valueKey, labelKey) {
  return items.map((item) => `<option value="${item[valueKey]}">${item[labelKey]}</option>`).join("");
}

function selectedCity() {
  return state.catalog?.cities.find((city) => city.cityId === bookingCity.value);
}

function selectedDistrict() {
  return selectedCity()?.districts.find((district) => district.districtId === bookingDistrict.value);
}

function renderCatalogOptions() {
  if (!state.catalog) return;
  bookingCity.innerHTML = options(state.catalog.cities, "cityId", "cityName");
  renderDistrictOptions();
  bookingDepartment.innerHTML = options(state.catalog.departments, "departmentId", "departmentName");
  renderMasterCatalogOptions();
}

function renderDistrictOptions() {
  const city = selectedCity() || state.catalog.cities[0];
  bookingDistrict.innerHTML = options(city.districts, "districtId", "districtName");
  renderHospitalOptions();
}

function renderHospitalOptions() {
  const district = selectedDistrict() || selectedCity()?.districts[0];
  bookingHospital.innerHTML = options(district?.hospitals || [], "hospitalId", "hospitalName");
}

function renderMasterCatalogOptions() {
  if (!state.catalog || !masterDepartment || !masterHospital) return;
  const hospitals = state.catalog.cities.flatMap((city) =>
    city.districts.flatMap((district) => district.hospitals)
  );
  masterDepartment.innerHTML = options(state.catalog.departments, "departmentId", "departmentName");
  masterHospital.innerHTML = options(hospitals, "hospitalId", "hospitalName");
}

function renderMasterDoctorList() {
  if (!masterDoctorList) return;
  masterDoctorList.innerHTML = `
    <h4>Kaydedilen Doktorlar</h4>
    <ul>
      ${state.doctors
        .map((doctor) => `
          <li>
            <strong>${doctor.doctorId} - Dr. ${doctor.firstName} ${doctor.lastName}</strong>
            <span>${doctor.departmentName} - ${doctor.hospitalName}</span>
            <em>Giris kodu: ${doctor.loginCode}</em>
          </li>
        `)
        .join("")}
    </ul>
  `;
}

function filteredBookingDoctors() {
  return state.doctors.filter((doctor) => {
    return (
      (!bookingCity.value || doctor.cityId === bookingCity.value) &&
      (!bookingDistrict.value || doctor.districtId === bookingDistrict.value) &&
      (!bookingHospital.value || doctor.hospitalId === bookingHospital.value) &&
      (!bookingDepartment.value || doctor.departmentId === bookingDepartment.value)
    );
  });
}

function renderDoctorOptions(doctors, preserveDoctorId = "") {
  bookingDoctor.innerHTML = doctors
    .map((doctor) => `<option value="${doctor.doctorId}">${doctor.doctorId} - Dr. ${doctor.firstName} ${doctor.lastName} (${doctor.departmentName})</option>`)
    .join("");
  if (preserveDoctorId && doctors.some((doctor) => doctor.doctorId === preserveDoctorId)) {
    bookingDoctor.value = preserveDoctorId;
  }
}

function renderDoctorLoginOptions(doctors) {
  doctorLoginSelect.innerHTML = doctors
    .map((doctor) => `<option value="${doctor.doctorId}">${doctor.doctorId} - Dr. ${doctor.firstName} ${doctor.lastName} (${doctor.departmentName})</option>`)
    .join("");
}

async function loadPortalDoctors() {
  const xml = await getXml("/api/portal/doctors");
  state.doctors = [...xml.querySelectorAll("doctors > doctor")].map(doctorFromNode);
  refreshBookingDoctorOptions();
  renderDoctorLoginOptions(state.doctors);
  renderClinics();
  renderMasterDoctorList();
}

function refreshBookingDoctorOptions() {
  renderDoctorOptions(filteredBookingDoctors(), bookingDoctor.value);
}

function selectDoctorContext(doctor) {
  if (!doctor) return;
  bookingCity.value = doctor.cityId;
  renderDistrictOptions();
  bookingDistrict.value = doctor.districtId;
  renderHospitalOptions();
  bookingHospital.value = doctor.hospitalId;
  bookingDepartment.value = doctor.departmentId;
  refreshBookingDoctorOptions();
  bookingDoctor.value = doctor.doctorId;
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
  if (statusFilter.value) params.set("status", statusFilter.value);
  if (doctorFilter.value.trim()) params.set("doctorId", doctorFilter.value.trim().toUpperCase());
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const xml = await getXml(`/api/appointments${suffix}`);
  renderAppointments([...xml.querySelectorAll("appointments > appointment")].map(appointmentFromNode));
}

function renderHolidays(xml) {
  holidaySource.textContent = text(xml, "source") || "XML service";
  holidayList.innerHTML = [...xml.querySelectorAll("holidays > holiday")]
    .slice(0, 6)
    .map((holiday) => `
      <li>
        <time datetime="${text(holiday, "date")}">${text(holiday, "date")}</time>
        <span>${text(holiday, "localName") || text(holiday, "name")}</span>
      </li>
    `)
    .join("");
}

function updateSessionLabels() {
  const patientText = state.patient
    ? `${state.patient.firstName} ${state.patient.lastName} (${state.patient.tc})`
    : "Hasta girişi yok";
  const doctorText = state.doctor
    ? `Dr. ${state.doctor.firstName} ${state.doctor.lastName} (${state.doctor.doctorId})`
    : "Doktor girişi yok";
  const masterText = state.master ? "Master girisi aktif" : "Master girisi yok";
  patientState.textContent = patientText;
  patientPanelState.textContent = patientText;
  doctorState.textContent = doctorText;
  doctorPanelState.textContent = doctorText;
  masterPanelState.textContent = masterText;
}

function slotLabel(slot) {
  return `${slot.date} ${slot.time}`;
}

function renderSlots(slots) {
  if (!state.patient) {
    slotGrid.innerHTML = '<p class="empty-state">Randevu seçmek için hasta girişi yapın.</p>';
    return;
  }
  if (!slots.length) {
    slotGrid.innerHTML = '<p class="empty-state">Bu filtrelere uygun doktor randevusu yok.</p>';
    return;
  }

  slotGrid.innerHTML = slots
    .map((slot) => {
      const bookedClass = slot.isBooked ? "booked" : "available";
      const action = slot.isBooked
        ? `<span>${slot.patient ? `${slot.patient.firstName} ${slot.patient.lastName}` : "Dolu"}</span>`
        : `<button class="slot-action" data-slot-id="${slot.slotId}" type="button">Randevu Al</button>`;
      return `
        <article class="slot-card ${bookedClass}">
          <strong>${slot.time}</strong>
          <span>${slot.doctorName}</span>
          <span>${slot.departmentName}</span>
          <small>${slot.hospitalName}</small>
          <small>${slot.isBooked ? "Dolu" : "Boş"}</small>
          ${action}
        </article>
      `;
    })
    .join("");
}

function renderBookingList(target, title, slots, includePatient) {
  if (!slots.length) {
    target.innerHTML = `<p class="empty-state">${title}: kayıt yok.</p>`;
    return;
  }

  target.innerHTML = `
    <h4>${title}</h4>
    <ul>
      ${slots
        .map((slot) => {
          const patient = slot.patient;
          const patientText = patient ? `${patient.firstName} ${patient.lastName} - TC: ${patient.tc}` : "Hasta bilgisi yok";
          return `
            <li>
              <strong>${slotLabel(slot)}</strong>
              <span>${slot.doctorName}</span>
              <span>${slot.departmentName} - ${slot.hospitalName}</span>
              ${includePatient ? `<em>${patientText}</em>` : ""}
              ${includePatient ? `<button class="button secondary cancel-booking" data-cancel-slot-id="${slot.slotId}" type="button">Randevuyu Iptal Et</button>` : ""}
            </li>
          `;
        })
        .join("")}
    </ul>
  `;
}

async function loadSlots() {
  const params = new URLSearchParams();
  if (bookingDoctor.value) params.set("doctorId", bookingDoctor.value);
  if (bookingCity.value) params.set("cityId", bookingCity.value);
  if (bookingDistrict.value) params.set("districtId", bookingDistrict.value);
  if (bookingHospital.value) params.set("hospitalId", bookingHospital.value);
  if (bookingDepartment.value) params.set("departmentId", bookingDepartment.value);
  if (bookingDate.value) params.set("date", bookingDate.value);
  const xml = await getXml(`/api/slots?${params.toString()}`);
  renderSlots([...xml.querySelectorAll("slots > slot")].map(slotFromNode));
}

async function loadPatientBookings() {
  if (!state.patientCredentials) {
    patientBookings.innerHTML = "";
    return;
  }
  const xml = await getXml(`/api/patient/bookings?${new URLSearchParams(state.patientCredentials).toString()}`);
  renderBookingList(patientBookings, "Randevularım", [...xml.querySelectorAll("appointments > appointment")].map(slotFromNode), false);
}

async function loadDoctorBookings() {
  if (!state.doctor || !state.doctorCode) {
    doctorBookings.innerHTML = "";
    return;
  }
  const params = new URLSearchParams({ doctorId: state.doctor.doctorId, code: state.doctorCode });
  const xml = await getXml(`/api/doctor/bookings?${params.toString()}`);
  renderBookingList(doctorBookings, "Randevu Alan Hastalar", [...xml.querySelectorAll("appointments > appointment")].map(slotFromNode), true);
}

patientRegisterForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formPayload(patientRegisterForm);
    const xml = await postForm("/api/auth/patient/register", payload);
    state.patient = patientFromNode(xml.querySelector("patient"));
    state.patientCredentials = { tc: payload.tc, birthDate: payload.birthDate };
    updateSessionLabels();
    await loadPatientBookings();
    await loadSlots();
    await loadSummary();
    showView("patient");
    showMessage("Hasta kaydı yapıldı ve giriş açıldı.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

patientLoginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formPayload(patientLoginForm);
    const xml = await postForm("/api/auth/patient/login", payload);
    state.patient = patientFromNode(xml.querySelector("patient"));
    state.patientCredentials = { tc: payload.tc, birthDate: payload.birthDate };
    updateSessionLabels();
    await loadPatientBookings();
    await loadSlots();
    await loadSummary();
    showView("patient");
    showMessage("Hasta girişi başarılı.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

doctorLoginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formPayload(doctorLoginForm);
    const xml = await postForm("/api/auth/doctor/login", payload);
    state.doctor = doctorFromNode(xml.querySelector("doctor"));
    state.doctorCode = payload.code;
    selectDoctorContext(state.doctor);
    updateSessionLabels();
    await loadDoctorBookings();
    showView("doctor");
    showMessage("Doktor girişi başarılı.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

masterLoginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = formPayload(masterLoginForm);
    const xml = await postForm("/api/auth/master/login", payload);
    state.master = { username: text(xml, "username") || payload.username };
    state.masterCredentials = payload;
    updateSessionLabels();
    renderMasterDoctorList();
    showView("master");
    showMessage("Master girisi basarili.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

doctorCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.masterCredentials) {
    showMessage("Doktor kaydetmek icin master girisi yapin.", "error");
    return;
  }
  try {
    const payload = {
      ...state.masterCredentials,
      ...formPayload(doctorCreateForm),
    };
    const xml = await postForm("/api/master/doctors", payload);
    const doctor = doctorFromNode(xml.querySelector("doctor"));
    await Promise.all([loadPortalDoctors(), loadSummary()]);
    doctorCreateForm.reset();
    renderMasterCatalogOptions();
    showMessage(`${doctor.doctorId} - Dr. ${doctor.firstName} ${doctor.lastName} kaydedildi.`, "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

slotCreateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.doctor || !state.doctorCode) {
    showMessage("Randevu oluşturmak için doktor girişi yapın.", "error");
    return;
  }
  try {
    const payload = {
      ...formPayload(slotCreateForm),
      doctorId: state.doctor.doctorId,
      code: state.doctorCode,
    };
    const xml = await postForm("/api/doctor/slots", payload);
    const slots = [...xml.querySelectorAll("slots > slot")].map(slotFromNode);
    selectDoctorContext(state.doctor);
    bookingDate.value = payload.date;
    await loadSlots();
    showMessage(`${slots.length} adet 15 dakikalık randevu oluşturuldu.`, "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

doctorBookings.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-cancel-slot-id]");
  if (!button) return;
  if (!state.doctor || !state.doctorCode) {
    showMessage("Randevu iptal etmek icin doktor girisi yapin.", "error");
    return;
  }
  try {
    await deleteForm(`/api/doctor/bookings/${button.dataset.cancelSlotId}`, {
      doctorId: state.doctor.doctorId,
      code: state.doctorCode,
    });
    await Promise.all([loadDoctorBookings(), loadSlots(), loadPublicBookings(), loadSummary()]);
    showMessage("Randevu iptal edildi.", "success");
  } catch (error) {
    showMessage(error.message, "error");
  }
});

slotGrid.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-slot-id]");
  if (!button) return;
  if (!state.patientCredentials) {
    showMessage("Randevu almak için hasta girişi yapın.", "error");
    return;
  }
  try {
    await postForm("/api/patient/appointments", {
      ...state.patientCredentials,
      slotId: button.dataset.slotId,
    });
    await Promise.all([loadSlots(), loadPatientBookings(), loadDoctorBookings(), loadPublicBookings(), loadSummary()]);
    showMessage("Randevu başarıyla alındı.", "success");
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

[bookingCity, bookingDistrict, bookingHospital, bookingDepartment].forEach((select) => {
  select.addEventListener("change", async () => {
    if (select === bookingCity) renderDistrictOptions();
    if (select === bookingCity || select === bookingDistrict) renderHospitalOptions();
    refreshBookingDoctorOptions();
    try {
      await loadSlots();
    } catch (error) {
      showMessage(error.message, "error");
    }
  });
});

loginRole.addEventListener("change", toggleAuthView);
applyFilters.addEventListener("click", loadAppointments);
doctorFilter.addEventListener("keydown", (event) => {
  if (event.key === "Enter") loadAppointments();
});

publicBookingsPagination.addEventListener("click", (event) => {
  const button = event.target.closest("[data-public-page]");
  if (!button) return;
  state.publicBookingPage = Number(button.dataset.publicPage);
  renderPublicBookings();
});

document.querySelectorAll("[data-view-target]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = button.dataset.viewTarget;
    if (target === "patient" && !state.patient) {
      showView("login");
      loginRole.value = "patient";
      toggleAuthView();
      return;
    }
    if (target === "doctor" && !state.doctor) {
      showView("login");
      loginRole.value = "doctor";
      toggleAuthView();
      return;
    }
    if (target === "master" && !state.master) {
      showView("login");
      loginRole.value = "master";
      toggleAuthView();
      return;
    }
    showView(target);
  });
});

async function loadSummary() {
  const summary = await getXml("/api/reports/summary");
  renderSummary(summary);
}

async function initializePortal() {
  bookingDate.value = todayIso();
  slotCreateForm.elements.date.value = todayIso();
  slotCreateForm.elements.startTime.value = "09:00";
  slotCreateForm.elements.endTime.value = "10:00";
  toggleAuthView();
  showView("home");
  renderCatalogOptions();
  refreshBookingDoctorOptions();
  renderDoctorLoginOptions(state.doctors);
  renderClinics();
  renderMasterDoctorList();
  updateSessionLabels();

  try {
    const [summary, holidays, catalog, portalDoctors] = await Promise.all([
      getXml("/api/reports/summary"),
      getXml("/api/integration/holidays?year=2026&countryCode=TR"),
      getXml("/api/portal/catalog"),
      getXml("/api/portal/doctors"),
    ]);

    state.catalog = catalogFromXml(catalog);
    state.doctors = [...portalDoctors.querySelectorAll("doctors > doctor")].map(doctorFromNode);
    renderSummary(summary);
    renderCatalogOptions();
    refreshBookingDoctorOptions();
    renderDoctorLoginOptions(state.doctors);
    renderClinics();
    renderMasterDoctorList();
    renderHolidays(holidays);
    updateSessionLabels();
    await Promise.all([loadAppointments(), loadSlots(), loadPublicBookings()]);
  } catch (error) {
    setText("#holidaySource", "XML API is not available");
    appointmentsTable.innerHTML = '<tr><td colspan="5">API server başlatılmalı.</td></tr>';
    publicBookingsTable.innerHTML = '<tr><td colspan="6">API server baslatilmali.</td></tr>';
    slotGrid.innerHTML = '<p class="empty-state">API server başlatılmalı.</p>';
  }
}

initializePortal();
