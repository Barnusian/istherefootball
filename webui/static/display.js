function getWeekSeed(date) {
  const monday = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const weekday = (monday.getDay() + 6) % 7;
  monday.setDate(monday.getDate() - weekday);
  const epochMonday = new Date(1970, 0, 5);
  return Math.floor((monday - epochMonday) / 604800000);
}

function getReceiptAngle(seed, multiplier, offset) {
  return ((seed * multiplier + offset) % 21) - 10;
}

function setWeeklyReceiptAngles() {
  const seed = getWeekSeed(new Date());
  const receipts = [
    [".receipt-this-week", getReceiptAngle(seed, 7, 0)],
    [".receipt-next-week", getReceiptAngle(seed, 13, 9)],
  ];

  for (const [selector, angle] of receipts) {
    document
      .querySelector(selector)
      .style.setProperty("--receipt-angle", `${angle}deg`);
  }
}

function showReceiptFallbacks() {
  for (const image of document.querySelectorAll(".paper img")) {
    image.addEventListener("error", () => {
      image.hidden = true;
      const fallback = image.nextElementSibling;
      fallback.textContent = image.dataset.fallback;
      fallback.hidden = false;
    });

    const imageUrl = new URL(image.src);
    imageUrl.searchParams.set("v", Date.now());
    image.src = imageUrl;
  }
}

function addPrintActions() {
  for (const button of document.querySelectorAll(".print-overlay")) {
    button.addEventListener("click", async () => {
      button.disabled = true;
      button.textContent = "PRINTING...";
      button.title = "";

      try {
        const response = await fetch("/api/print", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: button.dataset.image }),
        });
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.error || "Print request failed.");
        }
        button.textContent = "PRINT SENT";
      } catch (error) {
        button.textContent = "PRINT FAILED";
        button.title = error.message;
      } finally {
        window.setTimeout(() => {
          button.textContent = "PRINT NOW?";
          button.disabled = false;
        }, 3000);
      }
    });
  }
}

setWeeklyReceiptAngles();
showReceiptFallbacks();
addPrintActions();
