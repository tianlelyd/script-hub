function extractAllTablesToCSV() {
  const tables = Array.from(document.querySelectorAll("table"));
  if (tables.length === 0) {
    console.error("未找到任何表格");
    return;
  }

  let csvContent = "";
  tables.forEach((table, tableIndex) => {
    const rows = Array.from(table.querySelectorAll("tr"));
    const tableCsv = rows
      .map((row) => {
        const cells = Array.from(row.querySelectorAll("th, td"));
        return cells
          .map((cell) => {
            const textContent = cell.textContent?.trim() || "";
            return textContent.replace(/[\n\r\t,]/g, " ").replace(/"/g, '""');
          })
          .join(",");
      })
      .join("\n");

    csvContent += `Table ${tableIndex + 1}:\n${tableCsv}\n\n`;
  });

  const csvBlob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const csvUrl = URL.createObjectURL(csvBlob);

  const downloadLink = document.createElement("a");
  downloadLink.href = csvUrl;
  downloadLink.download = "all_tables_data.csv";
  document.body.appendChild(downloadLink);
  downloadLink.click();
  document.body.removeChild(downloadLink);
  URL.revokeObjectURL(csvUrl);
}

extractAllTablesToCSV();
