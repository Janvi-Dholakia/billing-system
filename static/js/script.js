function addRow() {
    let table = document.querySelector("#items tbody");
    let row = table.insertRow();

    let types = ["text", "number", "number", "number", "number", "number", "number"];

    for (let i = 0; i < 7; i++) {
        let cell = row.insertCell();
        let input = document.createElement("input");

        input.type = types[i];
        input.step = "any";

        if (i !== 0) input.oninput = calculate;

        cell.appendChild(input);
    }
}

function calculate() {
    let rows = document.querySelectorAll("#items tbody tr");
    let total = 0;

    rows.forEach(row => {
        let inputs = row.querySelectorAll("input");

        let net = parseFloat(inputs[1].value) || 0;
        let touch = parseFloat(inputs[2].value) || 0;
        let wastage = parseFloat(inputs[3].value) || 0;
        let labour = parseFloat(inputs[4].value) || 0;

        let silver = (net * touch) + wastage;
        let amount = net * labour;

        inputs[5].value = silver.toFixed(2);
        inputs[6].value = amount.toFixed(2);

        total += amount;
    });

    document.getElementById("total").innerText = total.toFixed(2);
}

function saveBill() {
    let rows = document.querySelectorAll("#items tbody tr");

    let items = [];

    rows.forEach(row => {
        let inputs = row.querySelectorAll("input");

        items.push({
            description: inputs[0].value,
            net_weight: inputs[1].value,
            touch: inputs[2].value,
            wastage: inputs[3].value,
            labour: inputs[4].value,
            silver: inputs[5].value,
            amount: inputs[6].value
        });
    });

    let data = {
        customer_name: document.getElementById("customer_name").value,
        place: document.getElementById("place").value,
        phone: document.getElementById("phone").value,
        date: document.getElementById("date").value,
        total: document.getElementById("total").innerText,
        items: items
    };

    fetch('/save_bill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(data => alert("Saved! " + data.bill_no));
}