(function () {
  const brl = (value) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number.isFinite(value) ? value : 0);
  const parseNumber = (value) => {
    let text = String(value || "").trim().replace(/R\$|\s/g, "");
    if (text.includes(",")) text = text.replace(/\./g, "").replace(",", ".");
    const number = Number(text);
    return Number.isFinite(number) && number >= 0 ? number : 0;
  };

  document.querySelectorAll("[data-custom-period]").forEach((button) => {
    button.addEventListener("click", () => {
      const form = button.closest("form");
      form.querySelector("[data-custom-fields]").classList.remove("d-none");
      form.querySelector("[data-custom-input]").disabled = false;
      form.querySelectorAll(".period-pills .btn").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
    });
  });

  const modal = document.getElementById("deleteModal");
  if (modal) {
    modal.addEventListener("show.bs.modal", (event) => {
      const trigger = event.relatedTarget;
      modal.querySelector("[data-delete-form]").action = trigger.dataset.deleteUrl;
      modal.querySelector("[data-delete-date-label]").textContent = trigger.dataset.deleteDate;
    });
  }

  const list = document.getElementById("expenseList");
  if (!list) return;
  const template = document.getElementById("expenseTemplate");
  const empty = document.getElementById("noExpenses");

  function calculate() {
    const revenue = parseNumber(document.getElementById("gross_revenue").value);
    const km = parseNumber(document.getElementById("kilometers").value);
    const expenses = [...document.querySelectorAll(".expense-amount")].reduce((sum, input) => sum + parseNumber(input.value), 0);
    const profit = revenue - expenses;
    document.getElementById("calcExpenses").textContent = brl(expenses);
    document.getElementById("calcProfit").textContent = brl(profit);
    document.getElementById("calcGrossKm").textContent = brl(km ? revenue / km : 0);
    document.getElementById("calcCostKm").textContent = brl(km ? expenses / km : 0);
    document.getElementById("calcProfitKm").textContent = brl(km ? profit / km : 0);
  }

  function addExpense(values = ["", "", ""]) {
    const row = template.content.firstElementChild.cloneNode(true);
    row.querySelector(".expense-category").value = values[0] || "";
    row.querySelector(".expense-description").value = values[1] || "";
    row.querySelector(".expense-amount").value = values[2] || "";
    row.querySelector(".remove-expense").addEventListener("click", () => {
      row.remove();
      empty.hidden = Boolean(list.children.length);
      calculate();
    });
    row.querySelector(".expense-amount").addEventListener("input", calculate);
    list.appendChild(row);
    empty.hidden = true;
  }

  document.getElementById("addExpense").addEventListener("click", () => addExpense());
  document.getElementById("gross_revenue").addEventListener("input", calculate);
  document.getElementById("kilometers").addEventListener("input", calculate);
  const initial = JSON.parse(document.getElementById("initialExpenses").textContent || "[]");
  initial.forEach(addExpense);
  if (!initial.length) empty.hidden = false;
  const dateInput = document.getElementById("date");
  if (!dateInput.value) dateInput.value = new Date().toLocaleDateString("en-CA");
  calculate();
})();

