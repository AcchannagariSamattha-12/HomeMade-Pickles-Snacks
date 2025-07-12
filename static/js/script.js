function updatePrice(select, index) {
  const weight = parseInt(select.value);
  const priceElement = document.getElementById("price-" + index);
  const basePrice = parseInt(priceElement.textContent.replace('₹', ''));
  const factor = weight / 250;
  const newPrice = basePrice * factor;
  priceElement.textContent = "₹" + newPrice.toFixed(2);
  document.getElementById("weight-" + index).value = weight;
}