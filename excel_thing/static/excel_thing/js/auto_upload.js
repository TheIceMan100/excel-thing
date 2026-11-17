document.querySelectorAll("[data-display-filename]").forEach((input) => {
  input.addEventListener("change", () => {
    const label = document.getElementById(input.dataset.displayFilename);
    if (label) {
      label.textContent = input.files[0]?.name ?? label.dataset.defaultText;
    }
  });
});

document.querySelectorAll("[data-submit-on-change]").forEach((input) => {
  input.addEventListener("change", () => {
    if (input.files.length > 0) {
      input.form.requestSubmit();
    }
  });
});

const demandDataElement = document.getElementById("demand-data");
if (demandDataElement) {
  const records = JSON.parse(demandDataElement.textContent);
  const materialSearch = document.getElementById("materialSearch");
  const sortSelect = document.getElementById("sortSelect");
  const recordTypeFilter = document.getElementById("recordTypeFilter");
  const workCenterFilter = document.getElementById("workCenterFilter");
  const workCenterOptions = document.getElementById("workCenterOptions");
  const startDate = document.getElementById("startDate");
  const endDate = document.getElementById("endDate");
  const dateError = document.getElementById("dateError");
  const viewToggle = document.getElementById("viewToggle");
  const tableWrap = document.getElementById("tableWrap");
  const calendarWrap = document.getElementById("calendarWrap");
  const groupedWrap = document.getElementById("groupedWrap");
  const emptyState = document.getElementById("emptyState");
  const inventoryResults = document.querySelector(".inventory-results");
  const resultsBody = document.getElementById("resultsBody");
  const calendarBody = document.getElementById("calendarBody");
  const groupedBody = document.getElementById("groupedBody");
  const calendarSummary = document.getElementById("calendarSummary");
  const groupedSummary = document.getElementById("groupedSummary");
  const resultsCount = document.getElementById("resultsCount");
  const statusText = document.getElementById("statusText");
  const viewButtons = [...document.querySelectorAll(".view-btn")];
  const dateValues = records.map((record) => record.calendar_day).sort();

  const asNumber = (value) => Number(value) || 0;
  const formatQuantity = (value) =>
    value.toLocaleString(undefined, {
      maximumFractionDigits: 3,
    });
  const appendRow = (body, values) => {
    const row = document.createElement("tr");
    values.forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value == null ? "" : String(value);
      row.appendChild(cell);
    });
    body.appendChild(row);
  };
  const clearResults = () => {
    resultsBody.replaceChildren();
    calendarBody.replaceChildren();
    groupedBody.replaceChildren();
  };

  if (records.length) {
    const minDate = dateValues[0];
    const maxDate = dateValues[dateValues.length - 1];
    startDate.min = minDate;
    startDate.max = maxDate;
    startDate.value = minDate;
    endDate.min = minDate;
    endDate.max = maxDate;
    endDate.value = maxDate;

    [materialSearch, sortSelect, recordTypeFilter, workCenterFilter, startDate, endDate]
      .forEach((control) => {
        control.disabled = false;
      });

    [...new Set(records.map((record) => record.record_type))]
      .sort((left, right) => left.localeCompare(right))
      .forEach((recordType) => {
        const option = document.createElement("option");
        option.value = recordType;
        option.textContent = recordType;
        recordTypeFilter.appendChild(option);
      });

    [...new Set(records.map((record) => record.work_center || "Unknown"))]
      .sort((left, right) => left.localeCompare(right))
      .forEach((workCenter) => {
        const option = document.createElement("option");
        option.value = workCenter;
        workCenterOptions.appendChild(option);
      });
  } else {
    viewToggle.hidden = true;
  }

  if (emptyState) {
    emptyState.hidden = records.length > 0 || Boolean(inventoryResults && !inventoryResults.hidden);
  }
  if (records.length) {
    viewToggle.hidden = false;
    tableWrap.hidden = false;
    if (statusText) {
      statusText.textContent = `${records.length} demand records loaded`;
    }
  }

  const getRange = () => {
    const from = startDate.value;
    const to = endDate.value;
    const valid = Boolean(from && to && from <= to);
    dateError.hidden = valid;
    dateError.textContent = valid
      ? ""
      : "Enter a valid date range with the start date on or before the end date.";
    return valid ? { from, to } : null;
  };

  const matchesTextFilters = (record) => {
    const materialQuery = materialSearch.value.trim().toLocaleLowerCase();
    const workCenterQuery = workCenterFilter.value.trim().toLocaleLowerCase();
    const material = record.material.toLocaleLowerCase();
    const workCenter = (record.work_center || "Unknown").toLocaleLowerCase();
    return (
      (!materialQuery || material.includes(materialQuery)) &&
      (!workCenterQuery || workCenter.includes(workCenterQuery))
    );
  };

  const getFilteredRecords = (range, includeRecordType = true) => {
    const selectedType = recordTypeFilter.value;
    return records.filter((record) => {
      const inRange =
        record.calendar_day >= range.from && record.calendar_day <= range.to;
      const typeMatches =
        !includeRecordType ||
        selectedType === "all" ||
        record.record_type === selectedType;
      return inRange && typeMatches && matchesTextFilters(record);
    });
  };

  const sortMaterials = (items, quantityFor) => {
    const sortMode = sortSelect.value;
    return [...items].sort((left, right) => {
      if (sortMode === "quantity-desc") {
        return quantityFor(right) - quantityFor(left) ||
          left.material.localeCompare(right.material);
      }
      if (sortMode === "quantity-asc") {
        return quantityFor(left) - quantityFor(right) ||
          left.material.localeCompare(right.material);
      }
      if (sortMode === "grouped") {
        return (
          left.work_center.localeCompare(right.work_center) ||
          left.material.localeCompare(right.material)
        );
      }
      return left.material.localeCompare(right.material);
    });
  };

  const renderTable = (range) => {
    const filteredRecords = getFilteredRecords(range);
    const sortMode = sortSelect.value;
    filteredRecords.sort((left, right) => {
      if (sortMode === "quantity-desc") {
        return asNumber(right.quantity) - asNumber(left.quantity) ||
          left.material.localeCompare(right.material);
      }
      if (sortMode === "quantity-asc") {
        return asNumber(left.quantity) - asNumber(right.quantity) ||
          left.material.localeCompare(right.material);
      }
      if (sortMode === "grouped") {
        return (
          left.work_center.localeCompare(right.work_center) ||
          left.material.localeCompare(right.material) ||
          left.calendar_day.localeCompare(right.calendar_day)
        );
      }
      return (
        left.material.localeCompare(right.material) ||
        left.calendar_day.localeCompare(right.calendar_day)
      );
    });
    filteredRecords.forEach((record) => {
      appendRow(resultsBody, [
        record.material,
        record.description,
        record.unit,
        record.record_type,
        record.work_center,
        record.calendar_day,
        formatQuantity(asNumber(record.quantity)),
      ]);
    });
    resultsCount.textContent = `${filteredRecords.length} records`;
  };

  const renderCalendar = (range) => {
    const materials = new Map();
    const relevantRecords = records.filter(matchesTextFilters);
    relevantRecords.forEach((record) => {
      const list = materials.get(record.material) || [];
      list.push(record);
      materials.set(record.material, list);
    });

    const availability = [];
    materials.forEach((materialRecords, material) => {
      const inRangeRecords = materialRecords.filter(
        (record) =>
          record.calendar_day >= range.from && record.calendar_day <= range.to
      );
      const stockRecords = materialRecords
        .filter(
          (record) =>
            record.record_type === "On-Hand Stock" &&
            record.calendar_day <= range.from
        )
        .sort((left, right) => right.calendar_day.localeCompare(left.calendar_day));
      const inRangeStock = materialRecords
        .filter(
          (record) =>
            record.record_type === "On-Hand Stock" &&
            record.calendar_day >= range.from &&
            record.calendar_day <= range.to
        )
        .sort((left, right) => left.calendar_day.localeCompare(right.calendar_day));
      const openingStock = stockRecords[0] || inRangeStock[0];
      if (!inRangeRecords.length && !openingStock) {
        return;
      }

      const representative = inRangeRecords[0] || openingStock;
      const totalQuantity = inRangeRecords.reduce((total, record) => {
        if (record.record_type === "Actual Requirements" || record.record_type === "Open Orders") {
          return total + asNumber(record.quantity);
        }
        return total;
      }, 0);
      const onHand = openingStock ? asNumber(openingStock.quantity) : 0;
      availability.push({
        material,
        description: representative.description,
        unit: representative.unit,
        work_center: representative.work_center,
        totalQuantity,
        onHand,
        difference: onHand + totalQuantity,
      });
    });

    const sorted = sortMaterials(availability, (item) => item.totalQuantity);
    sorted.forEach((item) => {
      appendRow(calendarBody, [
        item.material,
        item.description,
        item.unit,
        formatQuantity(item.totalQuantity),
        formatQuantity(item.onHand),
        formatQuantity(item.difference),
        `${range.from} to ${range.to}`,
      ]);
    });
    calendarSummary.textContent =
      `${sorted.length} materials; Total Quantity is net Open Orders and Actual Requirements, ` +
      "OnHand is the latest stock quantity on or before the range start (or the earliest in-range stock quantity if none exists), " +
      "and Difference is projected availability.";
    resultsCount.textContent = `${sorted.length} materials`;
  };

  const renderGrouped = (range) => {
    const filteredRecords = getFilteredRecords(range);
    const groups = new Map();
    filteredRecords.forEach((record) => {
      const workCenter = record.work_center || "Unknown";
      const group = groups.get(workCenter) || [];
      group.push(record);
      groups.set(workCenter, group);
    });

    const groupedRows = [...groups.entries()].map(([workCenter, groupRecords]) => {
      const materials = new Map();
      groupRecords.forEach((record) => {
        materials.set(
          record.material,
          (materials.get(record.material) || 0) + asNumber(record.quantity)
        );
      });
      const topMaterials = [...materials.entries()]
        .sort(
          (left, right) =>
            Math.abs(right[1]) - Math.abs(left[1]) ||
            left[0].localeCompare(right[0])
        )
        .slice(0, 5)
        .map(([material, quantity]) => `${material} (${formatQuantity(quantity)})`)
        .join(", ");
      const days = [...new Set(groupRecords.map((record) => record.calendar_day))].sort();
      return {
        workCenter,
        groupRecords,
        materialCount: materials.size,
        totalQuantity: groupRecords.reduce(
          (total, record) => total + asNumber(record.quantity),
          0
        ),
        activeDays: days.length,
        dateRange: days.length ? `${days[0]} to ${days[days.length - 1]}` : "",
        topMaterials,
      };
    });

    groupedRows.sort((left, right) => {
      if (sortSelect.value === "quantity-desc") {
        return right.totalQuantity - left.totalQuantity ||
          left.workCenter.localeCompare(right.workCenter);
      }
      if (sortSelect.value === "quantity-asc") {
        return left.totalQuantity - right.totalQuantity ||
          left.workCenter.localeCompare(right.workCenter);
      }
      return left.workCenter.localeCompare(right.workCenter);
    });

    groupedRows.forEach((group) => {
      appendRow(groupedBody, [
        group.workCenter,
        String(group.materialCount),
        formatQuantity(group.totalQuantity),
        String(group.groupRecords.length),
        String(group.activeDays),
        group.dateRange,
        group.topMaterials,
      ]);
    });
    const materialCount = groupedRows.reduce(
      (total, group) => total + group.materialCount,
      0
    );
    groupedSummary.textContent =
      `${groupedRows.length} work centers, ${materialCount} materials, ` +
      `${filteredRecords.length} records`;
    resultsCount.textContent = `${groupedRows.length} work centers`;
  };

  const render = () => {
    const range = getRange();
    const activeButton = viewButtons.find((button) =>
      button.classList.contains("is-active")
    );
    const view = activeButton?.dataset.view || "table";
    tableWrap.hidden = view !== "table" || !range;
    calendarWrap.hidden = view !== "calendar" || !range;
    groupedWrap.hidden = view !== "grouped" || !range;
    recordTypeFilter.disabled = view === "calendar";
    clearResults();
    if (!range) {
      calendarSummary.textContent = "";
      groupedSummary.textContent = "";
      resultsCount.textContent = "Invalid date range";
      return;
    }
    if (view === "calendar") {
      renderCalendar(range);
    } else if (view === "grouped") {
      renderGrouped(range);
    } else {
      renderTable(range);
    }
  };

  viewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      viewButtons.forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      render();
    });
  });
  [materialSearch, sortSelect, recordTypeFilter, workCenterFilter, startDate, endDate]
    .forEach((control) => {
      control.addEventListener("input", render);
      control.addEventListener("change", render);
    });

  if (records.length) {
    render();
  }
}
