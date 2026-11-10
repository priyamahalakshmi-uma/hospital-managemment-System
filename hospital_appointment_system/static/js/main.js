/* ==========================================================
   City Care Hospital - Frontend Application JavaScript
   ========================================================== */

document.addEventListener("DOMContentLoaded", function () {
    initBookingForm();
    initSlipModal();
});

// -------------------------------------------------------------
// 1. Patient Booking Form Logic
// -------------------------------------------------------------
function initBookingForm() {
    const form = document.getElementById("appointmentForm");
    if (!form) return;

    const doctorSelect = document.getElementById("doctor");
    const dateInput = document.getElementById("date");
    const selectedTimeInput = document.getElementById("selectedTime");
    const slotsGrid = document.getElementById("slotsGrid");
    const slotsMessage = document.getElementById("slotsMessage");

    // Set min date to today
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const todayStr = `${yyyy}-${mm}-${dd}`;
    dateInput.min = todayStr;

    // Fetch slots when doctor or date changes
    function checkSlots() {
        const doctor = doctorSelect.value;
        const date = dateInput.value;

        // Clear time selection
        selectedTimeInput.value = "";
        slotsGrid.innerHTML = "";
        slotsMessage.textContent = "";

        if (!doctor || !date) {
            slotsMessage.textContent = "Please select both doctor and date to view available time slots.";
            return;
        }

        // Sunday check
        const pickedDate = new Date(date + "T00:00:00");
        if (pickedDate.getDay() === 0) {
            slotsMessage.innerHTML = "<span style='color: #e63946; font-weight: bold;'>⚠️ Closed on Sundays. Please choose Monday through Saturday.</span>";
            return;
        }

        slotsMessage.textContent = "Loading available time slots...";

        fetch(`/api/available-slots?doctor=${encodeURIComponent(doctor)}&date=${encodeURIComponent(date)}`)
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    slotsMessage.textContent = data.message || "Failed to load slots.";
                    return;
                }

                if (data.closed) {
                    slotsMessage.innerHTML = `<span style='color: #e63946;'>⚠️ ${data.message}</span>`;
                    return;
                }

                if (!data.slots || data.slots.length === 0) {
                    slotsMessage.textContent = "No slots available for this date.";
                    return;
                }

                slotsMessage.textContent = "Click a time slot to select:";
                slotsGrid.innerHTML = "";

                data.slots.forEach(slot => {
                    const btn = document.createElement("button");
                    btn.type = "button";
                    btn.className = "slot-btn" + (slot.available ? "" : " booked");
                    btn.textContent = slot.time;
                    btn.title = slot.available ? "Available" : "Already Booked";
                    btn.disabled = !slot.available;

                    if (slot.available) {
                        btn.addEventListener("click", function () {
                            document.querySelectorAll(".slot-btn").forEach(b => b.classList.remove("selected"));
                            btn.classList.add("selected");
                            selectedTimeInput.value = slot.time;
                            document.getElementById("timeError").textContent = "";
                        });
                    }

                    slotsGrid.appendChild(btn);
                });
            })
            .catch(err => {
                console.error("Error fetching slots:", err);
                slotsMessage.textContent = "Unable to connect to server for slot availability.";
            });
    }

    doctorSelect.addEventListener("change", checkSlots);
    dateInput.addEventListener("change", checkSlots);

    // Only allow numbers in phone
    const phoneInput = document.getElementById("phone");
    phoneInput.addEventListener("input", function () {
        this.value = this.value.replace(/[^0-9]/g, "");
    });

    // Form submission
    form.addEventListener("submit", function (e) {
        e.preventDefault();

        // Clear error messages
        const fields = ["name", "email", "phone", "doctor", "date", "time", "reason"];
        fields.forEach(f => {
            const errEl = document.getElementById(f + "Error");
            if (errEl) errEl.textContent = "";
        });

        const name = document.getElementById("name").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const doctor = doctorSelect.value;
        const date = dateInput.value;
        const time = selectedTimeInput.value;
        const reason = document.getElementById("reason").value.trim();

        let valid = true;

        if (!name) {
            document.getElementById("nameError").textContent = "Please enter your full name.";
            valid = false;
        }

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email) {
            document.getElementById("emailError").textContent = "Please enter your email.";
            valid = false;
        } else if (!emailPattern.test(email)) {
            document.getElementById("emailError").textContent = "Please enter a valid email address.";
            valid = false;
        }

        const phonePattern = /^[0-9]{10}$/;
        if (!phone) {
            document.getElementById("phoneError").textContent = "Please enter your phone number.";
            valid = false;
        } else if (!phonePattern.test(phone)) {
            document.getElementById("phoneError").textContent = "Phone number must be exactly 10 digits.";
            valid = false;
        }

        if (!doctor) {
            document.getElementById("doctorError").textContent = "Please select a doctor.";
            valid = false;
        }

        if (!date) {
            document.getElementById("dateError").textContent = "Please select an appointment date.";
            valid = false;
        }

        if (!time) {
            document.getElementById("timeError").textContent = "Please select an available time slot above.";
            valid = false;
        }

        if (!reason) {
            document.getElementById("reasonError").textContent = "Please enter the reason for your visit.";
            valid = false;
        }

        if (!valid) return;

        // Submit to Flask Backend
        const submitBtn = document.getElementById("submitBtn");
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = "⏳ Booking Appointment...";

        const payload = {
            patient_name: name,
            email: email,
            phone: phone,
            doctor_name: doctor,
            appointment_date: date,
            appointment_time: time,
            reason: reason
        };

        fetch("/api/appointments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json().then(data => ({ status: res.status, body: data })))
        .then(({ status, body }) => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;

            if (status === 201 && body.success) {
                // Show printable slip modal
                showAppointmentSlip(body.appointment);
                form.reset();
                selectedTimeInput.value = "";
                slotsGrid.innerHTML = "";
                slotsMessage.textContent = "";
            } else {
                alert(body.message || "Failed to book appointment. Please check details.");
            }
        })
        .catch(err => {
            console.error("Booking submission error:", err);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
            alert("Network or server error. Please ensure Flask server is running.");
        });
    });
}

// -------------------------------------------------------------
// 2. Printable Appointment Slip Modal Logic
// -------------------------------------------------------------
function initSlipModal() {
    const modal = document.getElementById("slipModal");
    if (!modal) return;

    const closeBtn = document.getElementById("modalCloseBtn");
    const doneBtn = document.getElementById("modalDoneBtn");
    const printBtn = document.getElementById("modalPrintBtn");

    function closeModal() {
        modal.classList.remove("active");
    }

    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (doneBtn) doneBtn.addEventListener("click", closeModal);

    modal.addEventListener("click", function (e) {
        if (e.target === modal) closeModal();
    });

    if (printBtn) {
        printBtn.addEventListener("click", function () {
            window.print();
        });
    }
}

function showAppointmentSlip(appointment) {
    const modal = document.getElementById("slipModal");
    if (!modal) return;

    document.getElementById("slipRefId").textContent = appointment.reference_id;
    document.getElementById("slipPatientName").textContent = appointment.patient_name;
    document.getElementById("slipPhone").textContent = appointment.phone;
    document.getElementById("slipEmail").textContent = appointment.email;
    document.getElementById("slipDoctor").textContent = appointment.doctor_name;
    document.getElementById("slipDate").textContent = appointment.appointment_date;
    document.getElementById("slipTime").textContent = appointment.appointment_time;
    document.getElementById("slipReason").textContent = appointment.reason;
    document.getElementById("slipStatus").textContent = appointment.status;

    modal.classList.add("active");
}

// -------------------------------------------------------------
// 3. Quick Doctor Select & Smooth Scroll Helper
// -------------------------------------------------------------
function selectDoctorAndScroll(doctorName) {
    const docSelect = document.getElementById("doctor");
    if (!docSelect) return;

    docSelect.value = doctorName;
    docSelect.dispatchEvent(new Event("change"));

    const appointmentSection = document.getElementById("appointmentForm");
    if (appointmentSection) {
        appointmentSection.scrollIntoView({ behavior: "smooth", block: "center" });
        const dateInput = document.getElementById("date");
        if (dateInput) {
            setTimeout(() => dateInput.focus(), 500);
        }
    }
}

