const API = "http://127.0.0.1:5000/api";
const form = document.getElementById("bookingForm");
const message = document.getElementById("bookingMessage");
const rows = document.getElementById("bookingRows");
const distanceInput = form.elements.distance;
const vehicleInput = form.elements.vehicle;
const fareEstimate = document.getElementById("fareEstimate");
const rates = {Bike:{base:20,per:8},Mini:{base:50,per:12},Sedan:{base:80,per:16},SUV:{base:120,per:22}};
let latestBooking = null;

function money(value){return "₹" + Number(value).toFixed(2)}
function calculateFare(){
  const rate = rates[vehicleInput.value] || rates.Mini;
  const km = Math.max(0, Number(distanceInput.value) || 0);
  fareEstimate.textContent = money(rate.base + km * rate.per);
}
distanceInput.addEventListener("input", calculateFare);
vehicleInput.addEventListener("change", calculateFare);

async function api(path, options={}){
  const response = await fetch(API + path, {
    ...options,
    headers: {"Content-Type":"application/json", ...(options.headers || {})}
  });
  const data = await response.json().catch(()=>({error:"Unexpected server response."}));
  if(!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}

function escapeHtml(value){
  return String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
}

async function loadBookings(){
  rows.innerHTML = '<tr><td colspan="6" class="empty-row">Loading bookings…</td></tr>';
  try{
    const bookings = await api("/bookings");
    if(!bookings.length){
      rows.innerHTML = '<tr><td colspan="6" class="empty-row">No bookings yet — create your first demo booking above.</td></tr>';
      return;
    }
    rows.innerHTML = bookings.map(b => `
      <tr>
        <td>${escapeHtml(b.id)}</td>
        <td class="route-cell">${escapeHtml(b.pickup)}<small>↓ ${escapeHtml(b.destination)}</small></td>
        <td>${escapeHtml(b.vehicle)}</td><td>${money(b.fare)}</td>
        <td><span class="status-pill">${escapeHtml(b.status)}</span></td>
        <td><button class="table-action" data-receipt="${escapeHtml(b.id)}">View ↗</button></td>
      </tr>`).join("");
  }catch(error){
    rows.innerHTML = `<tr><td colspan="6" class="empty-row">Can't reach backend. Start the Flask server on port 5000.</td></tr>`;
  }
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true; submit.textContent = "Creating booking…"; message.textContent = "";
  const data = Object.fromEntries(new FormData(form).entries());
  data.distance = Number(data.distance);
  try{
    latestBooking = await api("/bookings", {method:"POST", body:JSON.stringify(data)});
    message.textContent = `Booking ${latestBooking.id} confirmed! Your receipt is ready.`;
    form.reset(); distanceInput.value = "5"; vehicleInput.value = "Mini"; calculateFare();
    await loadBookings();
    showReceipt(latestBooking);
  }catch(error){
    message.textContent = error.message;
  }finally{
    submit.disabled = false; submit.innerHTML = 'Confirm demo booking <span>→</span>';
  }
});

function showReceipt(b){
  if(!b){alert("Create a booking first, or choose a receipt from booking history.");return}
  const date = new Date(b.created_at).toLocaleString();
  document.getElementById("receiptContent").innerHTML = `
    <h2>SmartBooking</h2><div class="receipt-sub">DIGITAL TRIP RECEIPT · DEMO COPY</div>
    <div class="receipt-line"><span>Booking ID</span><strong>${escapeHtml(b.id)}</strong></div>
    <div class="receipt-line"><span>Passenger</span><strong>${escapeHtml(b.customer)}</strong></div>
    <div class="receipt-line"><span>Pickup</span><strong>${escapeHtml(b.pickup)}</strong></div>
    <div class="receipt-line"><span>Destination</span><strong>${escapeHtml(b.destination)}</strong></div>
    <div class="receipt-line"><span>Distance</span><strong>${escapeHtml(b.distance)} km</strong></div>
    <div class="receipt-line"><span>Ride type</span><strong>${escapeHtml(b.vehicle)}</strong></div>
    <div class="receipt-line"><span>Assigned driver</span><strong>${escapeHtml(b.driver)}</strong></div>
    <div class="receipt-line"><span>Booking status</span><strong>${escapeHtml(b.status)}</strong></div>
    <div class="receipt-line"><span>Payment</span><strong>${escapeHtml(b.payment_status)}</strong></div>
    <div class="receipt-line"><span>Created</span><strong>${escapeHtml(date)}</strong></div>
    <div class="receipt-line receipt-total"><span>Total fare</span><strong>${money(b.fare)}</strong></div>
    <div class="receipt-foot">Thank you for trying SmartBooking. This is a student demonstration; no real payment was collected.</div>`;
  document.getElementById("receiptDialog").showModal();
}
rows.addEventListener("click", async event => {
  const button = event.target.closest("[data-receipt]");
  if(!button) return;
  try{showReceipt(await api("/bookings/" + encodeURIComponent(button.dataset.receipt)))}
  catch(error){alert(error.message)}
});
document.getElementById("latestReceiptBtn").addEventListener("click", () => showReceipt(latestBooking));
document.getElementById("closeReceipt").addEventListener("click", () => document.getElementById("receiptDialog").close());
document.getElementById("printReceipt").addEventListener("click", () => window.print());
document.getElementById("refreshBtn").addEventListener("click", loadBookings);

document.getElementById("aiForm").addEventListener("submit", async event => {
  event.preventDefault();
  const question = document.getElementById("aiQuestion");
  const answer = document.getElementById("aiAnswer");
  const button = document.getElementById("aiButton");
  button.disabled = true; button.textContent = "Thinking…"; answer.textContent = "Connecting to Gemma through Ollama…";
  try{
    const result = await api("/ai", {method:"POST", body:JSON.stringify({question:question.value.trim()})});
    answer.textContent = result.answer || "No answer returned.";
  }catch(error){
    answer.textContent = error.message + " If the AI is unavailable, the booking system still works.";
  }finally{
    button.disabled = false; button.textContent = "Ask AI ↗";
  }
});

calculateFare();
loadBookings();
