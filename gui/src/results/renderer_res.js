// ------------------------------------------------------------------------
// Declare All Variables
// ------------------------------------------------------------------------
let filePath = null;
let selectedRowValue = null;
let isMappingTable = false;
let lastSelectedRowValue = null;
let mzRowMap = new Map();
let DeconTableMzSet;
const DeconTable_MATCH_COLOR = '#E6A7B2';

// Global variables for main table data, sorting, filtering, pagination, and deletion.
let mainTableData = [];
let currentSort = { column: null, order: 'asc' };
let rowsPerPage = 200;
let currentPage = 1;
let rowsToDelete = [];


// ------ Helper Functions ----------

// Format Decimals to 4 Places. This allows many values to be mapped across tables / plots.
function formatDecimalValue(value) {
  if (typeof value === 'number' && !Number.isInteger(value)) {
    return value.toFixed(4);
  }
  return value;
}

// Set DIA width of columns. (Plots)
function getDIAWidth(mzValue, DeconTableMzSet) {
  const existsInDeconTable = DeconTableMzSet.has(mzValue.toFixed(4));
  if (existsInDeconTable) {
      return 2;  
  } else {
      return 1; 
  }
}

// Generate Normal Distribution Data for fitted lines in Plots
function generateGaussianData(mean, height, width) {
  mean = parseFloat(mean);
  width = parseFloat(width); 
  height = parseFloat(height);
  if (isNaN(mean) || isNaN(width) || isNaN(height)) {
      console.error("Invalid input values");
      return [];
  }
  const data = [];
  const start = mean - 2 * width;
  const end = mean + 2 * width;
  const step = 4 * width / 100;
  for(let x = start; x <= end; x += step) {
      let y = height * Math.exp(-Math.pow(x - mean, 2) / (0.3606 * width * width));
      data.push([x, y]);
  }
  return data;
}

// Select Decon Table Row. Called on clicked from Bidirectional Plot
function selectDeconTableRow(mzValue) {
  const tableRow = mzRowMap.get(parseFloat(mzValue).toFixed(4));
  if (tableRow) {
      // Deselect previously selected row (if any)
      const selectedRows = document.querySelectorAll('.selected-row');
      selectedRows.forEach(row => row.classList.remove('selected-row'));
      // Select the current row
      tableRow.classList.add('selected-row');
      tableRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

// ------------------------------------------------------------------------
// Table Creation Functions
// ------------------------------------------------------------------------


// Display Main Table
function showMainTable(data) {
  // Store full dataset globally.
  mainTableData = data;
  
  const tableContainer = document.getElementById('main-table-container');
  tableContainer.innerHTML = ''; 
  tableContainer.style.border = "1px solid black";
  
  // Create and insert the filter panel (pinned to top).
  const filterPanel = createFilterPanel();
  tableContainer.appendChild(filterPanel);
  
  // If no column has been sorted yet, sort by the first available column ascending.
  if (!currentSort.column && data.length > 0) {
    const headers = Object.keys(data[0]).filter(header => 
      header !== "dia_decon_frag_ids" &&
      header !== "dia_xic" &&
      header !== "dia_atd" &&
      header !== "dia_dt" &&
      header !== "dia_dt_pkht" &&
      header !== "dia_dt_fwhm" &&
      header !== "dia_rt_pkht" &&
      header !== "dia_rt_fwhm" &&
      header !== "dia_rt_psnr" &&
      header !== "dda_rt_pkht" &&
      header !== "dda_rt_fwhm" &&
      header !== "dda_rt_psnr" &&
      header !== "dda_rt" &&
      header !== "dda_ms2_peaks" &&
      header !== "dia_ms2_peaks" &&
      header !== "dia_dt_fwhm" &&
      header !== "dia_dt_psnr" &&
      header !== "dia_ms1"
    );
    if (headers.length > 0) {
      currentSort.column = headers[0];
      currentSort.order = 'asc';
      data.sort((a, b) => {
        let aVal = parseFloat(a[currentSort.column]) || a[currentSort.column];
        let bVal = parseFloat(b[currentSort.column]) || b[currentSort.column];
        if (aVal < bVal) return -1;
        if (aVal > bVal) return 1;
        return 0;
      });
    }
  }
  
  // Render the main table.
  renderMainTable(data);
}

// Render Main Table
function renderMainTable(data) {
  const tableContainer = document.getElementById('main-table-container');
  // Remove any existing table (but keep the filter panel).
  const existingTable = document.getElementById('main-table');
  // Remove previous delete selections
  rowsToDelete = [];
  updateDeleteButtonVisibility();

  if (existingTable) existingTable.remove();
  
  const table = document.createElement('table');
  table.id = 'main-table';
  table.style.border = "1px solid black";
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');
  
  // Build headers.
  const headers = Object.keys(data[0]).filter(header => 
      header !== "dia_decon_frag_ids" &&
      header !== "dia_xic" &&
      header !== "dia_atd" &&
      header !== "dia_dt" &&
      header !== "dia_dt_pkht" &&
      header !== "dia_dt_fwhm" &&
      header !== "dia_rt_pkht" &&
      header !== "dia_rt_fwhm" &&
      header !== "dia_rt_psnr" &&
      header !== "dda_rt_pkht" &&
      header !== "dda_rt_fwhm" &&
      header !== "dda_rt_psnr" &&
      header !== "dda_rt" &&
      header !== "dda_ms2_peaks" &&
      header !== "dia_ms2_peaks" &&
      header !== "dia_dt_fwhm" &&
      header !== "dia_dt_psnr" &&
      header !== "dia_ms1"
  );
  
  const headerRow = document.createElement('tr');
  headers.forEach(header => {
    const th = document.createElement('th');
    th.style.border = '1px solid black';
    th.textContent = header;
    // Create span for sort icon.
    const sortIcon = document.createElement('span');
    sortIcon.style.marginLeft = '5px';
    if (header === currentSort.column) {
      sortIcon.textContent = currentSort.order === 'asc' ? '↑' : '↓';
    }
    th.appendChild(sortIcon);
    
    // When header is clicked, perform sort.
    th.addEventListener('click', () => {
      // Clear sort icons from all header cells.
      for (let child of headerRow.children) {
        child.lastChild.textContent = '';
      }
      if (currentSort.column === header) {
        currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
      } else {
        currentSort.column = header;
        currentSort.order = 'asc';
      }
      data.sort((a, b) => {
        let aVal = parseFloat(a[header]) || a[header];
        let bVal = parseFloat(b[header]) || b[header];
        if (aVal < bVal) return currentSort.order === 'asc' ? -1 : 1;
        if (aVal > bVal) return currentSort.order === 'asc' ? 1 : -1;
        return 0;
      });
      // Set the current header's sort icon.
      sortIcon.textContent = currentSort.order === 'asc' ? '↑' : '↓';
      debouncedRenderBody(data, tbody, headers);
    });
    
    headerRow.appendChild(th);
  });
  // Add an extra header cell for the delete column.
  const deleteTh = document.createElement('th');
  deleteTh.textContent = "Delete Row";
  deleteTh.style.textAlign = 'center';
  headerRow.appendChild(deleteTh);
  
  thead.appendChild(headerRow);
  
  // Make the header sticky (position it below the filter panel).
  const filterPanel = document.getElementById('filter-panel');
  if (filterPanel) {
    thead.style.position = 'sticky';
    thead.style.top = (filterPanel.offsetHeight - 1) + 'px';
    thead.style.backgroundColor = '#fff';
    thead.style.zIndex = '900';
    thead.style.border = '1px solid black';
  }
  
  table.appendChild(thead);
  
  // Render table body.
  renderTableBody(data, tbody, headers);
  table.appendChild(tbody);
  tableContainer.appendChild(table);
  
  // Render pagination controls (pinned to bottom).
  renderPaginationControls(data);
}

// Debounce wrapper for re-rendering the table body.
const debouncedRenderBody = debounce(renderTableBody, 300);

// Uses a DocumentFragment to build rows
function renderTableBody(data, tbody, headers) {
  tbody.innerHTML = '';
  const fragment = document.createDocumentFragment();
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = Math.min(data.length, currentPage * rowsPerPage);
  
  for (let i = startIndex; i < endIndex; i++) {
    const row = data[i];
    const tableRow = document.createElement('tr');
    tableRow.dataset.id = row['dia_pre_id']; // store id for later use
    
    headers.forEach(header => {
      const td = document.createElement('td');
      td.textContent = formatDecimalValue(row[header]);
      tableRow.appendChild(td);
    });
    
    // Create an extra cell for the delete (red X) icon.
    const deleteCell = document.createElement('td');
    deleteCell.style.textAlign = 'center';
    deleteCell.style.cursor = 'pointer';
    deleteCell.style.color = 'red';
    deleteCell.textContent = '✖';
    deleteCell.addEventListener('click', (e) => {
      e.stopPropagation();
      const id = tableRow.dataset.id; // This is a string.
      const index = rowsToDelete.indexOf(id);
      if (index === -1) {
        rowsToDelete.push(id);
        tableRow.style.backgroundColor = '#ffcccc';
      } else {
        rowsToDelete.splice(index, 1);
        tableRow.style.backgroundColor = '';
      }
      updateDeleteButtonVisibility();
    });


    tableRow.appendChild(deleteCell);
    // Attach the original row click event (for updating details)
    tableRow.addEventListener('click', () => {
      window.activeTableElement = document.getElementById('main-table-container');
      // Remove previous "selected" (for details) but do not clear red-delete highlight.
      const previousSelectedRow = tbody.querySelector('.selected');
      if (previousSelectedRow) {
        previousSelectedRow.classList.remove('selected');
      }
      tableRow.classList.add('selected');
      
      selectedRowValue = { id: row['dia_pre_id'] };
      
      // Update detail fields.
      const mzValueElement = document.getElementById('mz');
      const DIArtValueElement = document.getElementById('rt');
      const dtValueElement = document.getElementById('dt');
      const DTpkhtValueElement = document.getElementById('dt_pkht');
      const DTfwhmValueElement = document.getElementById('dt_fwhm');
      const DTpsnrValueElement = document.getElementById('dt_psnr');
      const DIArtPKHTValueElement = document.getElementById('rt_pkht');
      const DIArtFWHMValueElement = document.getElementById('rt_fwhm');
      const DIArtPSNRValueElement = document.getElementById('rt_psnr');
      const DDArtValueElement = document.getElementById('dda_rt_value');
      const DDArtPKHTValueElement = document.getElementById('dda_rt_pkht_value');
      const DDArtFWHMValueElement = document.getElementById('dda_rt_fwhm_value');
      const DDArtPSNRValueElement = document.getElementById('dda_rt_psnr_value');
      const PreDIAatdValueElement = document.getElementById('dia_atd_value');
      const PreDIAxicValueElement = document.getElementById('dia_xic_value');
      
      mzValueElement.textContent = formatDecimalValue(row['mz']);
      DIArtValueElement.textContent = formatDecimalValue(row['rt']);
      dtValueElement.textContent = formatDecimalValue(row['dt']);
      DTpkhtValueElement.textContent = formatDecimalValue(row['dt_pkht']);
      DTfwhmValueElement.textContent = formatDecimalValue(row['dt_fwhm']);
      DTpsnrValueElement.textContent = formatDecimalValue(row['dia_dt_psnr']);
      DIArtPKHTValueElement.textContent = formatDecimalValue(row['rt_pkht']);
      DIArtFWHMValueElement.textContent = formatDecimalValue(row['rt_fwhm']);
      DIArtPSNRValueElement.textContent = formatDecimalValue(row['rt_psnr']);
      DDArtValueElement.textContent = formatDecimalValue(row['dda_rt']);
      DDArtPKHTValueElement.textContent = formatDecimalValue(row['dda_rt_pkht']);
      DDArtFWHMValueElement.textContent = formatDecimalValue(row['dda_rt_fwhm']);
      DDArtPSNRValueElement.textContent = formatDecimalValue(row['dda_rt_psnr']);
      PreDIAatdValueElement.textContent = row['dia_xic'];
      PreDIAxicValueElement.textContent = row['dia_atd'];
      
      // Prevent annotation table flicker
      document.getElementById('annotation-table').innerHTML = "";

      // Send IPC messages.
      window.api.send('fetch-mapping-table', selectedRowValue);
      let currentFeatId = selectedRowValue.id;
      window.api.send('fetch-raw-blob', { featId: currentFeatId, rawType: 'DIA_PRE_MS1' });
      window.api.send('fetch-dia-ms2', currentFeatId);
      const currentDIA_mz = parseFloat(row['mz']);
      window.api.send('fetch-dda-features', { diaMz: currentDIA_mz, tolerance: 0.01 });
      
      // Clear decon plots and request decon fragments.
      clearDeconPlots();
      window.api.send('fetch-decon-fragments', currentFeatId);
      window.api.send('fetch-raw-blob', { featId: currentFeatId, rawType: 'DIA_PRE_XIC' });
      window.api.send('fetch-raw-blob', { featId: currentFeatId, rawType: 'DIA_PRE_ATD' });

      if (filePath) {
        window.api.send('fetch-annotation-table', filePath);
    }
      
      const resultsDisplay = document.getElementById('below-table-content');
      resultsDisplay.style.display = 'block';
      
      const diaFeatureIdColumn = row['DIA Feature ID'];
      if (diaFeatureIdColumn !== undefined) {
        findInAnnTableByFeatureId(diaFeatureIdColumn);
      }
    });
    
    // Hover effects.
    tableRow.addEventListener('mouseover', () => {
      tableRow.classList.add('hover');
    });
    tableRow.addEventListener('mouseout', () => {
      tableRow.classList.remove('hover');
    });
    
    fragment.appendChild(tableRow);
  }
  tbody.appendChild(fragment);
  renderPaginationControls(data);
}


// Called in Main Table. Select mapped rows in Annotation Table
function findInAnnTableByFeatureId(featureId) {
  const AnnContainer = document.getElementById('annotation-table');
  const rows = AnnContainer.querySelectorAll('tr');

      // Deselect all previously selected rows first
  rows.forEach(row => {
        if (row.classList.contains('selected')) {
            row.classList.remove('selected');
        }
    });

  rows.forEach(row => {
      // Assuming the feature ID is in the first column
      const featureIdCell = row.children[1];
      if (featureIdCell && parseInt(featureIdCell.textContent, 10) === featureId) {
        // row.dispatchEvent(new Event('click', { 'bubbles': true }));  
        row.classList.add('selected'); 
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
  });
}

// Pagination!
// Renders and pins pagination controls to the bottom.
function renderPaginationControls(data) {
  const oldPagination = document.getElementById('pagination-controls');
  if (oldPagination) oldPagination.remove();
  
  const totalPages = Math.ceil(data.length / rowsPerPage);
  if (totalPages <= 1) return;
  
  const paginationContainer = document.createElement('div');
  paginationContainer.id = 'pagination-controls';
  paginationContainer.style.marginTop = '0px';
  paginationContainer.style.position = 'sticky';
  paginationContainer.style.bottom = '0';
  paginationContainer.style.top = '1';
  paginationContainer.style.background = '#fff';
  paginationContainer.style.zIndex = '1000';
  paginationContainer.style.fontSize = '0.8em';

  const prevButton = document.createElement('button');
  prevButton.textContent = 'Prev';
  prevButton.style.fontSize = '0.8em';
  prevButton.disabled = currentPage === 1;
  prevButton.addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      renderMainTable(data);
    }
  });
  paginationContainer.appendChild(prevButton);
  
  const pageIndicator = document.createElement('span');
  pageIndicator.style.margin = '0 10px';
  pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
  paginationContainer.appendChild(pageIndicator);
  
  const nextButton = document.createElement('button');
  nextButton.textContent = 'Next';
  nextButton.style.fontSize = '0.8em';
  nextButton.disabled = currentPage === totalPages;
  nextButton.addEventListener('click', () => {
    if (currentPage < totalPages) {
      currentPage++;
      renderMainTable(data);
    }
  });
  paginationContainer.appendChild(nextButton);
  
  const tableContainer = document.getElementById('main-table-container');
  tableContainer.appendChild(paginationContainer);
}

// FILTER Option 
// Creates a filter panel pinned to the top with no background.
function createFilterPanel() {
  const container = document.createElement('div');
  container.id = 'filter-panel';
  container.style.position = 'sticky';
  container.style.top = '0';
  container.style.padding = '2px';
  // Set background to a light color if desired.
  container.style.background = 'whitesmoke';
  container.style.zIndex = '1000';
  container.style.display = 'flex';
  container.style.justifyContent = 'space-between';
  container.style.alignItems = 'center';
  
  // Left side: filter controls.
  const filterControls = document.createElement('div');
  filterControls.appendChild(document.createTextNode('Filter: '));
  
  const columnSelect = document.createElement('select');
  if (mainTableData.length > 0) {
    const headers = Object.keys(mainTableData[0]).filter(header =>
      header !== "dia_decon_frag_ids" &&
      header !== "dia_xic" &&
      header !== "dia_atd" &&
      header !== "dia_dt" &&
      header !== "dia_dt_pkht" &&
      header !== "dia_dt_fwhm" &&
      header !== "dia_rt_pkht" &&
      header !== "dia_rt_fwhm" &&
      header !== "dia_rt_psnr" &&
      header !== "dda_rt_pkht" &&
      header !== "dda_rt_fwhm" &&
      header !== "dda_rt_psnr" &&
      header !== "dda_rt" &&
      header !== "dda_ms2_peaks" &&
      header !== "dia_ms2_peaks" &&
      header !== "dia_dt_pkht" &&
      header !== "dia_dt_psnr" &&
      header !== "dia_ms1"
    );
    headers.forEach(col => {
      const option = document.createElement('option');
      option.value = col;
      option.textContent = col;
      columnSelect.appendChild(option);
    });
  }
  
  const minInput = document.createElement('input');
  minInput.type = 'number';
  minInput.placeholder = 'Min value';
  const maxInput = document.createElement('input');
  maxInput.type = 'number';
  maxInput.placeholder = 'Max value';
  
  const filterButton = document.createElement('button');
  filterButton.textContent = 'Filter';
  filterButton.addEventListener('click', debounce(() => {
    const selectedColumn = columnSelect.value;
    // Default to -Infinity/Infinity if blank.
    const minVal = minInput.value === '' ? -Infinity : parseFloat(minInput.value);
    const maxVal = maxInput.value === '' ? Infinity : parseFloat(maxInput.value);
    const filteredData = mainTableData.filter(row => {
      const cellVal = parseFloat(row[selectedColumn]);
      return cellVal >= minVal && cellVal <= maxVal;
    });
    currentPage = 1;
    renderMainTable(filteredData);
  }, 300));
  
  // Allow user to press Enter in either input field to trigger the filter.
  [minInput, maxInput].forEach(input => {
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        filterButton.click();
      }
    });
  });
  
  const resetButton = document.createElement('button');
  resetButton.textContent = 'Reset Filter';
  resetButton.addEventListener('click', () => {
    currentPage = 1;
    renderMainTable(mainTableData);
  });
  
  filterControls.appendChild(columnSelect);
  filterControls.appendChild(minInput);
  filterControls.appendChild(maxInput);
  filterControls.appendChild(filterButton);
  filterControls.appendChild(resetButton);
  
  const deleteBtn = document.createElement('button');
  deleteBtn.id = 'delete-rows-button';
  deleteBtn.textContent = 'Delete Values from SQL Database';
  deleteBtn.style.display = 'none';
  deleteBtn.style.fontSize = '0.8em';
  deleteBtn.addEventListener('click', () => {
    if (window.confirm(`Are you sure you want to delete the selected DIA Precursors from the SQL Database?\n\nThis can not be reverted.`)) {
      // Send IPC to main process to delete the rows.
      window.api.send('delete-diaprecursor-rows', rowsToDelete);
    }
  });
  
  container.appendChild(filterControls);
  container.appendChild(deleteBtn);
  
  return container;
}


function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function updateDeleteButtonVisibility() {
  const deleteBtn = document.getElementById('delete-rows-button');
  if (rowsToDelete.length > 0) {
    deleteBtn.style.display = 'inline-block';
  } else {
    deleteBtn.style.display = 'none';
  }
}

function clearDeconPlots() {
  document.getElementById('decon-xic-plot').innerHTML = "";
  document.getElementById('decon-atd-plot').innerHTML = "";
  const deconTableContainer = document.getElementById('deconvoluted-frags-table');
  if (deconTableContainer) {
    deconTableContainer.innerHTML = "";
  }
  window.deconBlobData = {};
}

window.api.receive('delete-diaprecursor-rows-result', (result) => {
  if (result.success) {
    // Convert each row's id to a string before comparing.
    mainTableData = mainTableData.filter(row => !rowsToDelete.includes(String(row['dia_pre_id'])));
    rowsToDelete = [];
    updateDeleteButtonVisibility();
    renderMainTable(mainTableData);
  } else {
    alert("Deletion failed: " + result.error);
  }
});


// Create Deconvoluted Feature Table
function showDeconTable(fragments) {
  const tableContainer = document.getElementById('deconvoluted-frags-table');
  tableContainer.innerHTML = ''; // Clear previous content
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');

  const headers = ["Fragment ID", "XIC Dist", "ATD Dist"];
  const headerRow = document.createElement('tr');
  headers.forEach(header => {
    const th = document.createElement('th');
    th.textContent = header;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  fragments.forEach(fragment => {
    const row = document.createElement('tr');
    // Create cells for each column:
    const fragIdCell = document.createElement('td');
    fragIdCell.textContent = fragment.dia_frag_id;
    const xicDistCell = document.createElement('td');
    xicDistCell.textContent = formatDecimalValue(fragment.xic_dist);
    const atdDistCell = document.createElement('td');
    atdDistCell.textContent = formatDecimalValue(fragment.atd_dist);
    row.appendChild(fragIdCell);
    row.appendChild(xicDistCell);
    row.appendChild(atdDistCell);

    // When a decon fragment row is clicked:
    row.addEventListener('click', () => {
      window.activeTableElement = document.getElementById('deconvoluted-frags-table');
      // Deselect any previously selected row:
      const selectedRows = tbody.querySelectorAll('.selected-row');
      selectedRows.forEach(r => r.classList.remove('selected-row'));
      row.classList.add('selected-row');
      processDeconFragmentRowData(fragment);
    });
    tbody.appendChild(row);
  });

  table.appendChild(thead);
  table.appendChild(tbody);
  tableContainer.appendChild(table);

  // Automatically select the first row if it exists:
  if (tbody.firstChild) {
    tbody.firstChild.click();
  }
}

// Global array for annotated feature deletions
let lipidRowsToDelete = [];

// Helper: update the visibility of the delete button for the annotation table.
function updateAnnotationDeleteButtonVisibility() {
  const deleteBtn = document.getElementById('delete-annotated-button');
  if (!deleteBtn) return; // Button not created yet, so nothing to update.
  if (lipidRowsToDelete.length > 0) {
    deleteBtn.style.display = 'inline-block';
  } else {
    deleteBtn.style.display = 'none';
  }
}
// Updated function to build the annotated features table with a delete column.
function showAnnotationTable(data) {
  lipidRowsToDelete = [];
  updateAnnotationDeleteButtonVisibility();

  const tableContainer = document.getElementById('annotation-table');
  tableContainer.innerHTML = '';

  // If no annotation data was returned, show a message.
  if (!data || data.length === 0) {
    tableContainer.innerHTML = "<p>No Lipids found for selected DIA Precursor.</p>";
    return;
  }

  // Filter data based on the selected main table row’s dia_pre_id.
  if (selectedRowValue && selectedRowValue.id) {
    data = data.filter(row => row.dia_pre_id == selectedRowValue.id);
  }
  if (data.length === 0) {
    tableContainer.innerHTML = "<p>No Lipids found for selected DIA Precursor.</p>";
    return;
  }

  // Build the table.
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');

  // Create headers using all keys from the first row.
  // Then add an extra header cell for deletion.
  const headers = Object.keys(data[0]);
  const headerRow = document.createElement('tr');
  headers.forEach(header => {
    const th = document.createElement('th');
    th.textContent = header;
    headerRow.appendChild(th);
  });
  const deleteHeader = document.createElement('th');
  deleteHeader.textContent = "Delete Row";
  deleteHeader.style.textAlign = "center";
  headerRow.appendChild(deleteHeader);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  // Create table rows.
  data.forEach((row) => {
    const tr = document.createElement('tr');
    tr.dataset.lipidId = row.lipid_id || row[Object.keys(row)[0]];

    // Create cells for each header.
    headers.forEach(header => {
      const td = document.createElement('td');
      td.textContent = row[header];
      tr.appendChild(td);
    });

    // Create an extra cell for the delete (red "✖") icon.
    const deleteCell = document.createElement('td');
    deleteCell.style.textAlign = 'center';
    deleteCell.style.cursor = 'pointer';
    deleteCell.style.color = 'red';
    deleteCell.textContent = '✖';
    deleteCell.addEventListener('click', (e) => {
      // Prevent the row’s click event from firing.
      e.stopPropagation();
      const lipidId = tr.dataset.lipidId;
      const index = lipidRowsToDelete.indexOf(lipidId);
      if (index === -1) {
        lipidRowsToDelete.push(lipidId);
        tr.style.backgroundColor = '#ffcccc';
      } else {
        lipidRowsToDelete.splice(index, 1);
        tr.style.backgroundColor = '';
      }
      updateAnnotationDeleteButtonVisibility();
    });
    tr.appendChild(deleteCell);

    // Add a click event for row selection.
    tr.addEventListener('click', () => {
      // Mark this table as active for keyboard navigation.
      window.activeTableElement = document.getElementById('annotation-table');
      // Remove any previous selection.
      const prev = tableContainer.querySelector('.selected-row');
      if (prev) prev.classList.remove('selected-row');
      tr.classList.add('selected-row');
      // Extract the lipid ID.
      const lipidId = tr.dataset.lipidId;
      console.log("Annotation table row selected. Lipid ID:", lipidId);
      // Send IPC message to fetch lipid fragment details for this lipid.
      window.api.send('fetch-lipid-fragment-details', lipidId);
    });

    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  tableContainer.appendChild(table);
  // Set this annotation table as the active table by default.
  window.activeTableElement = tableContainer;
  // Optionally auto-select the first row.
  if (tbody.firstChild) {
    tbody.firstChild.click();
  }

  // Create (or update) a delete button for annotated features if it doesn't exist.
  let deleteBtn = document.getElementById('delete-annotated-button');
  if (!deleteBtn) {
    deleteBtn = document.createElement('button');
    deleteBtn.id = 'delete-annotated-button';
    deleteBtn.textContent = 'Delete Annotated Features from SQL';
    deleteBtn.style.fontSize = '0.8em';
    deleteBtn.style.display = 'none';
    deleteBtn.addEventListener('click', () => {
      if (window.confirm("Are you sure you want to delete the selected annotated features? This action cannot be undone.")) {
        // Send the lipidRowsToDelete array to the main process.
        window.api.send('delete-annotated-feature-rows', lipidRowsToDelete);
      }
    });
    // Insert the button above the annotation table.
    tableContainer.parentElement.insertBefore(deleteBtn, tableContainer);
  }
}

// ------------------------------------------------------------------------
// Plot Functions
// ------------------------------------------------------------------------

// Decon Plot Generation (both plots generated here)
function displayDeconPlots(xicPairs, atdPairs, PreXicPairs, PreAtdPairs) {
  const normalize = pairs => {
    const maxValue = Math.max(...pairs.map(pair => pair[1]));
    return pairs.map(pair => [pair[0], pair[1] / maxValue]);
  };

// Normalize each set of pairs independently
  xicPairs = normalize(xicPairs);
  atdPairs = normalize(atdPairs);
  PreXicPairs = normalize(PreXicPairs);
  PreAtdPairs = normalize(PreAtdPairs);
  
  const chartOptions = {
    chart: {
      backgroundColor: 'transparent',
      style: {
          fontFamily: 'Arial, sans-serif'
      },
      borderWidth: 0,
      shadow: false,
      zoomType: 'xy',
      panning: true,
      resetZoomButton: {
        position: {
            align: 'left', 
            verticalAlign: 'top', 
            x: 0,
            y: 0
        },
        theme: {
          width: 40,   
          height: 10, 
          style: {
              fontSize: '8px', 
          }}
  }},
    title: {
        style: {
            fontWeight: 'bold',
            fontSize: '16px'
        }
    },
    xAxis: {
        gridLineColor: '#E8E8E8',
        labels: {
            style: {
                fontSize: '12px'
            }
        }
    },
    yAxis: {
        gridLineColor: '#E8E8E8',
        labels: {
            style: {
                fontSize: '12px'
            }
        }
    },
    tooltip: {
        borderWidth: 0,
        backgroundColor: 'rgba(220,220,220,0.8)',
        shadow: false,
        style: {
            fontSize: '12px'
        }
    },
    legend: {
      align: 'right',       
      verticalAlign: 'top',   
      layout: 'vertical',
      floating: true,      // Allow legend to overlap chart 
      x: -10,                
      y: -10                  
  },
    credits: {
        enabled: false
    }
  };

  // Decon XIC Plot
  Highcharts.chart('decon-xic-plot', {

      ...chartOptions,
      title: null,
      series: [{
          data: xicPairs,
          type: 'spline',
          name: 'XIC Fragment',
          color: '#FF4500',
          marker: {
            radius: 2,
            fillColor: '#FF4500',
            enabled: false
        }
      },
      {
        data: PreXicPairs,
        type: 'spline',
        name: 'XIC precursor',
        color: '#00457C',
        marker: {
          radius: 2,
          fillColor: '#00457C',
          enabled: false
      }
    }],
      xAxis: {
          ...chartOptions.xAxis,
          title: {
              text: 'Retention Time'
          }
      },
      yAxis: {
          ...chartOptions.yAxis,
          title: {
              text: 'Intensity'
          }
      }
  });

  // Decon ATD Plot
  Highcharts.chart('decon-atd-plot', {
      ...chartOptions,
      title: null,
      series: [{
          data: atdPairs,
          type: 'spline',
          name: 'ATD fragment',
          color: '#FF4500'
      },
      {
        data: PreAtdPairs,
        type: 'spline',
        name: 'ATD precursor',
        color: '#00457C',
        marker: {
          radius: 2,
          fillColor: '#00457C',
          enabled: false
      }
    }
    ],
      xAxis: {
          ...chartOptions.xAxis,
          title: {
              text: 'Arrival Time'
          }
      },
      yAxis: {
          ...chartOptions.yAxis,
          title: {
              text: 'Intensity'
          }
      }
  });
}


// ATD Plot Generation
function displayATDPlot(atdPairs) {
  // ATD Plot
  const chartOptions = {
    chart: {
        backgroundColor: 'transparent',
        style: {
            fontFamily: 'Arial, sans-serif'
        },
        borderWidth: 0,
        shadow: false,
        zoomType: 'xy',
        panning: true,
        resetZoomButton: {
          position: {
              align: 'left', 
              verticalAlign: 'top', 
              x: 0,
              y: 0
          },
          theme: {
            width: 40,   
            height: 10, 
            style: {
                fontSize: '8px', 
                // padding: '2px 2px' 
            }}
    }},
    exporting: {
      enabled: true,
      buttons: {
          contextButton: {
              menuItems: ['downloadPNG', 'downloadJPEG', 'downloadPDF', 'downloadSVG']
          }
      }
  },
    title: {
        style: {
            fontWeight: 'bold',
            fontSize: '16px'
        }
    },
    
    xAxis: {
        gridLineColor: '#E8E8E8',
        labels: {
            style: {
                fontSize: '12px'
            }
        }
    },
    yAxis: {
        gridLineColor: '#E8E8E8',
        labels: {
            style: {
                fontSize: '12px'
            }
        }
    },
    tooltip: {
        borderWidth: 0,
        backgroundColor: 'rgba(220,220,220,0.8)',
        shadow: false,
        style: {
            fontSize: '12px'
        }
    },
    legend: {
      align: 'right',     
      verticalAlign: 'top',  
      layout: 'vertical',
      floating: true,        
      x: -10,      
      y: -10                
  },
    credits: {
        enabled: false
    }
};


Highcharts.chart('arrival-time-plot', {
    ...chartOptions,
    title: null,
    series: [{
        data: atdPairs,
        type: 'spline',
        name: 'ATD Data',
        color: '#00457C',
        marker: {
          radius: 2,
          fillColor: '#00457C',
          enabled: false
      }
    },
    {
      data: generateGaussianData(
          document.getElementById('dt').textContent,
          document.getElementById('dt_pkht').textContent,
          document.getElementById('dt_fwhm').textContent
        ),
      type: 'line',
      name: 'Fit (DIA)',
      color: 'black', 
      dashStyle: 'dash',
      marker: {
          enabled: false
      }
    },
    ],
    xAxis: {
        ...chartOptions.xAxis,
        title: {
            text: 'Arrival Time (ms)'
        }
    },
    yAxis: {
        ...chartOptions.yAxis,
        title: {
            text: 'Intensity'
        }
    }
});
}

// Xic Plot Generation
function displayXicPlot(xicPairs) {
  // XIC Plot
  const chartOptions = {
    chart: {
      backgroundColor: 'transparent',
      style: {
          fontFamily: 'Arial, sans-serif'
      },
      borderWidth: 0,
      shadow: false,
      zoomType: 'xy',
      panning: true,
      resetZoomButton: {
        position: {
            align: 'left', 
            verticalAlign: 'top', 
            x: 0,
            y: 0
        },
        theme: {
          width: 40,   
          height: 10, 
          style: {
              fontSize: '8px', 
          }}
  }},
    title: {
        style: {
            fontWeight: 'bold',
            fontSize: '16px'
        }
    },
    xAxis: {
        gridLineColor: '#E8E8E8',
        labels: {
            style: {
                fontSize: '12px'
            }
        }
    },
    yAxis: {
        gridLineColor: '#E8E8E8',
        labels: {
            style: {
                fontSize: '12px'
            }
        }
    },
    tooltip: {
        borderWidth: 0,
        backgroundColor: 'rgba(220,220,220,0.8)',
        shadow: false,
        style: {
            fontSize: '12px'
        }
    },
    legend: {
      align: 'right',       
      verticalAlign: 'top',  
      layout: 'vertical',
      floating: true,       
      x: -10,               
      y: -10                  
  },
    credits: {
        enabled: false
    }
};


window.icpPlot = Highcharts.chart('ion-chromatogram-plot', {
    ...chartOptions,
    title: null,
    series: [{
      data: xicPairs,
      type: 'spline',
      name: 'Raw DIA',
      color: '#00457C',
      marker: {
          radius: 2,
          fillColor: '#00457C',
          enabled: false
      }
  },
  {
      data: generateGaussianData(
            document.getElementById('rt').textContent, 
            document.getElementById('rt_pkht').textContent, 
            document.getElementById('rt_fwhm').textContent
            ),
      type: 'line',
      name: 'Fit (DIA)',
      color: 'black', 
      dashStyle: 'dash',
      marker: {
          enabled: false
      }
  },
  {
    name: 'Fit (DDA)',
    data: [],
    type: 'line',
    color: '#808080',
    dashStyle: 'dash',
    marker: { enabled: false }
  },
  ],
    xAxis: {
        ...chartOptions.xAxis,
        title: {
            text: 'Retention Time (min)'
        }
    },
    yAxis: {
        ...chartOptions.yAxis,
        title: {
            text: 'Intensity'
        }
    }
});
}

// MS1 Plot Generation
function displayMS1Plot(ms1Pairs) {
  const xValue = parseFloat(document.getElementById('mz').textContent);
  const maxYValue = ms1Pairs.reduce((max, pair) => Math.max(max, pair[1]), 0);
  const chartOptions = {
    chart: {
      backgroundColor: 'transparent',
      style: {
          fontFamily: 'Arial, sans-serif'
      },
      borderWidth: 0,
      shadow: false,
      zoomType: 'xy',
      panning: true,
      resetZoomButton: {
        position: {
            align: 'left', 
            verticalAlign: 'top', 
            x: 0,
            y: 0
        },
        theme: {
          width: 40,   
          height: 10, 
          style: {
              fontSize: '8px', 
          }}
  }},
    title: {
        style: {
            fontWeight: 'bold',
            fontSize: '16px'
        }
    },
    xAxis: {
        gridLineColor: '#E8E8E8',
        labels: {
            style: {
                fontSize: '12px'
            }
        }
  },
    yAxis: {
        gridLineColor: '#E8E8E8',
        labels: {
            style: {
                fontSize: '12px'
            }
        }
    },
    tooltip: {
        borderWidth: 0,
        backgroundColor: 'rgba(220,220,220,0.8)',
        shadow: false,
        style: {
            fontSize: '12px'
        }
    },
    legend: {
      align: 'right',         
      verticalAlign: 'top',   
      layout: 'vertical',
      floating: true,         
      x: -10,               
      y: -10           
  },
    credits: {
        enabled: false
    }
};
Highcharts.chart('ms1-plot', {
  ...chartOptions,
  title: null,
  series: [{
      data: ms1Pairs,
      type: 'spline',
      name: 'DIA MS1',
      color: '#00457C',
      marker: {
          radius: 2,
          fillColor: '#00457C',
          enabled: false
      }
  },
  {
      type: 'line',
      name: 'm/z',
      data: [[xValue, 0], [xValue, maxYValue]], 
      color: 'grey',
      dashStyle: 'Dash'  
  }],
  xAxis: {
      ...chartOptions.xAxis,
      title: {
          text: 'm/z'
      }
  },
  yAxis: {
      ...chartOptions.yAxis,
      title: {
          text: 'Intensity'
      },
      max: maxYValue  
  }
});
}


function updateDDAChromatogramPlot() {
  const dda_rt = document.getElementById('dda_rt_value').textContent;
  const dda_rt_pkht = document.getElementById('dda_rt_pkht_value').textContent;
  const dda_rt_fwhm = document.getElementById('dda_rt_fwhm_value').textContent;
  
  console.log(`Updating DDA fit: rt=${dda_rt}, pkht=${dda_rt_pkht}, fwhm=${dda_rt_fwhm}`);
  
  // Generate the Gaussian data using these parameters.
  const newSeriesData = generateGaussianData(dda_rt, dda_rt_pkht, dda_rt_fwhm);
  
  // Use the globally stored chart reference.
  const chart = window.icpPlot;
  if (chart) {
    // Check if a series for the DDA fit already exists.
    const existing = chart.series.find(s => s.name === 'Fit (DDA)');
    if (existing) {
      existing.setData(newSeriesData, true);
    } else {
      chart.addSeries({
        name: 'Fit (DDA)',
        data: newSeriesData,
        type: 'line',
        color: '#808080',
        dashStyle: 'dash',
        marker: { enabled: false }
      }, true);
    }
  } else {
    console.warn("Ion chromatogram chart not found.");
  }
}

window.diaMs2Data = null;
window.ddaMs2Data = null;

function showDDAFeaturesTable(features) {
  const container = document.getElementById('dda-features-table');
  container.innerHTML = ''; 

  if (!features || features.length === 0) {
    container.innerHTML = '<p>No matching DDA features found.</p>';
    return;
  }

  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');

  // Define headers to display.
  const headers = ["dda_pre_id", "mz", "dda_rt", "dda_rt_pkht", "dda_rt_fwhm"];
  const headerRow = document.createElement('tr');
  headers.forEach(header => {
    const th = document.createElement('th');
    th.textContent = header;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);

  features.forEach((feature, idx) => {
    const row = document.createElement('tr');
    headers.forEach(header => {
      const td = document.createElement('td');
      td.textContent = feature[header];
      row.appendChild(td);
    });
    row.addEventListener('click', () => {
      // Clear any previously selected rows
      window.activeTableElement = document.getElementById('dda-features-table');
      const prev = container.querySelector('.selected');
      if (prev) prev.classList.remove('selected');
      row.classList.add('selected');

      // Update UI elements with DDA values.
      document.getElementById('dda_rt_value').textContent = feature.dda_rt;
      document.getElementById('dda_rt_pkht_value').textContent = feature.dda_rt_pkht;
      document.getElementById('dda_rt_fwhm_value').textContent = feature.dda_rt_fwhm;
      
      // Request the DDA MS2 spectrum for the selected DDA feature.
      const ddaFeatureId = feature['dda_pre_id'];
      window.api.send('fetch-dda-ms2', ddaFeatureId);
      updateDDAChromatogramPlot();
    });

    tbody.appendChild(row);

    // Automatically select the first row:
    if (idx === 0) {
      setTimeout(() => { row.click(); }, 0);
    }
  });
  table.appendChild(tbody);
  container.appendChild(table);
}


function plotBidirectionalMS2(ddaData, diaData) {
  // Ensure inputs are arrays.
  ddaData = Array.isArray(ddaData) ? ddaData : [];
  diaData = Array.isArray(diaData) ? diaData : [];
  console.log("plotBidirectionalMS2 called with:", ddaData, diaData);

  if (ddaData.length === 0 && diaData.length === 0) {
    document.getElementById("bidirectional-plot").style.display = "none";
    document.getElementById("error-message-bidirectional-plot").style.display = "block";
    return;
  } else {
    document.getElementById("bidirectional-plot").style.display = "block";
    document.getElementById("error-message-bidirectional-plot").style.display = "none";
  }
  
  // Compute combined m/z values.
  const combinedMzValues = Array.from(new Set([
    ...ddaData.map(peak => peak.fmz),
    ...diaData.map(peak => peak.fmz)
  ])).sort((a, b) => a - b);

  const dataMin = Math.min(...combinedMzValues);
  const dataMax = Math.max(...combinedMzValues);
  const buffer = (dataMax - dataMin) * 0.05;
  
  // Compute maximum absolute intensity.
  const maxDDA = ddaData.length ? Math.max(...ddaData.map(peak => Math.abs(peak.fint))) : 0;
  const maxDIA = diaData.length ? Math.max(...diaData.map(peak => Math.abs(peak.fint))) : 0;
  const maxAbs = Math.max(maxDDA, maxDIA);
  
  window.DeconTableMzSet = new Set(
    Array.from(document.querySelectorAll('#deconvoluted-frags-table tbody tr td:first-child'))
      .map(cell => parseFloat(cell.innerText).toFixed(4))
  );
  
  // Create the bidirectional chart.
  window.bidirectionalChart = Highcharts.chart('bidirectional-plot', {
    chart: {
      type: 'column',
      backgroundColor: null,
      zoomType: 'xy',
      panning: true,
      resetZoomButton: {
        position: { align: 'left', verticalAlign: 'top', x: 0, y: 0 }
      }
    },
    credits: { enabled: false },
    title: { text: 'DDA & DIA MS2 Peaks' },
    legend: {
      align: 'right',
      verticalAlign: 'top',
      layout: 'vertical',
      floating: true,
      x: -10,
      y: -10
    },
    tooltip: {
      formatter: function () {
        let baseText = 'm/z: ' + this.x + '<br/>Intensity: ' + Math.abs(this.y);
        if (this.series.name === 'DIA' && this.point.dia_frag_id && window.lipidFragmentDetails) {
          const details = window.lipidFragmentDetails[String(this.point.dia_frag_id)];
          if (details) {
            baseText += '<br/>Frag Rule: ' + details.frag_rule;
            baseText += '<br/>Supports FA: ' + details.supports_fa;
          }
        }
        return baseText;
      }
    },
    xAxis: {
      type: 'linear',
      min: dataMin - buffer,
      max: dataMax + buffer,
      title: { text: 'm/z' },
      ignoreHiddenSeries: true
    },
    yAxis: [{
      title: { text: 'DDA Intensity' },
      min: -maxAbs,
      max: 0,
      labels: { formatter: function () { return Math.abs(this.value); } },
      top: '50%',
      height: '50%',
      offset: 0,
      lineWidth: 1
    }, {
      title: { text: 'DIA Intensity' },
      min: 0,
      max: maxAbs,
      labels: { formatter: function () { return this.value; } },
      top: '0%',
      height: '50%',
      offset: 0,
      lineWidth: 1
    }],
    plotOptions: {
      column: {
        grouping: false,
        pointPlacement: 'on',
        pointPadding: 0,
        borderWidth: 0,
        shadow: false,
        allowPointSelect: true,
        states: { select: { color: '#800080' } }
      },
      series: { cursor: 'pointer' }
    },
    series: [{
      name: 'DDA',
      yAxis: 0,
      data: ddaData.map(peak => ({
        x: peak.fmz,
        y: -peak.fint,
        color: "#7cb5ec"
      })),
      grouping: false,
      pointPlacement: 'on',
      pointWidth: 2,
      legendIndex: 2
    }, {
      name: 'DIA',
      yAxis: 1,
      data: diaData.map(peak => {
        const isSelected = window.selectedLipidFragmentID &&
                           (String(peak.dia_frag_id) === String(window.selectedLipidFragmentID));
        return {
          x: peak.fmz,
          y: peak.fint,
          color: "#BFA6BF",
          pointWidth: 2,
          dia_frag_id: peak.dia_frag_id,
          borderWidth: isSelected ? 2 : 0,
          borderColor: isSelected ? "#FF0000" : undefined,
          dataLabels: {
            enabled: true,
            formatter: function () {
              const key = String(this.point.dia_frag_id);
              const details = window.lipidFragmentDetails ? window.lipidFragmentDetails[key] : undefined;
              if (details && parseInt(details.diagnostic, 10) === 1) {
                return '↓';
              }
              return '';
            },
            verticalAlign: 'top',
            y: 0,
            style: { fontSize: '12px', fontWeight: 'bold' }
          }
        };
      }),
      grouping: false,
      pointPlacement: 'on',
      legendIndex: 1
    }]
  },
  function(chart) {
    chart.series.forEach(series => {
      if (series.name === 'DIA') {
        series.points.forEach(point => {
          if (point.dataLabel && point.textStr === '↓') {
            point.dataLabel.attr({ y: point.shapeArgs.y - 2 });
          }
        });
      }
    });
  });
}

//  Decon stuff
window.api.receive('decon-fragments-result', (data) => {
  const deconTableContainer = document.getElementById('deconvoluted-frags-table');
  const errorMessageElement = document.getElementById('error-message');
  if (data.error) {
    deconTableContainer.style.display = "none";
    errorMessageElement.textContent = "Error fetching decon fragments: " + data.error;
    return;
  }
  if (!data.fragments || data.fragments.length === 0) {
    deconTableContainer.style.display = "none";
    errorMessageElement.textContent = "No deconvoluted DIA fragments found for feature.";
  } else {
    errorMessageElement.textContent = "";
    deconTableContainer.style.display = "block";
    showDeconTable(data.fragments);
    window.activeTableElement = document.getElementById('main-table-container');
  }
});


function processDeconFragmentRowData(fragment) {

  // Clear any previous decon blob data
  window.deconBlobData = {};

  // Request the raw blob data for the decon fragment.
  window.api.send('fetch-decon-raw-blob', { featId: fragment.dia_frag_id, rawType: 'DIA_FRAG_XIC' });
  window.api.send('fetch-decon-raw-blob', { featId: fragment.dia_frag_id, rawType: 'DIA_FRAG_ATD' });
}

window.api.receive('decon-raw-blob-result', (data) => {
  if (data.error) {
    console.error("Error fetching decon raw blob for", data.rawType, data.error);
    return;
  }
  window.deconBlobData = window.deconBlobData || {};
  window.deconBlobData[data.rawType] = data.data;

  // Only proceed if both decon fragment and precursor data are available.
  if (
    window.deconBlobData['DIA_FRAG_XIC'] && window.deconBlobData['DIA_FRAG_ATD'] &&
    window.precursorXICData && window.precursorATDData
  ) {
    // Convert the raw blob data to (x, y) pairs.
    const fragXICPairs = window.deconBlobData['DIA_FRAG_XIC'].x.map((x, i) => [x, window.deconBlobData['DIA_FRAG_XIC'].y[i]]);
    const fragATDPairs = window.deconBlobData['DIA_FRAG_ATD'].x.map((x, i) => [x, window.deconBlobData['DIA_FRAG_ATD'].y[i]]);
    const precursorXICPairs = window.precursorXICData.x.map((x, i) => [x, window.precursorXICData.y[i]]);
    const precursorATDPairs = window.precursorATDData.x.map((x, i) => [x, window.precursorATDData.y[i]]);

    // Call your plot function with fragment data and precursor data.
    displayDeconPlots(fragXICPairs, fragATDPairs, precursorXICPairs, precursorATDPairs);
  }
});


function updateSelectedDIAHighlight() {
  if (window.bidirectionalChart && window.bidirectionalChart.series) {
    // Find the DIA series (we assume its name is "DIA")
    const diaSeries = window.bidirectionalChart.series.find(s => s.name === 'DIA');
    if (diaSeries) {
      diaSeries.points.forEach(point => {
        // Determine if this point should be highlighted.
        const isSelected = window.selectedLipidFragmentID && 
                           (String(point.dia_frag_id) === String(window.selectedLipidFragmentID));
        // Update the point border. The update() method here will modify the point's graphic.
        point.update({
          borderWidth: isSelected ? 2 : 0,
          borderColor: isSelected ? "#FF0000" : null
        }, false);
        // For diagnostic points, adjust the dataLabel (the down arrow).
        if (point.dataLabel) {
          // Check if the formatter returns the down arrow.
          const key = String(point.dia_frag_id);
          const details = window.lipidFragmentDetails ? window.lipidFragmentDetails[key] : undefined;
          if (details && parseInt(details.diagnostic, 10) === 1) {
            // Use the shapeArgs of the point to position the arrow just above the bar.
            // Get the height of the dataLabel (if available)
            const bbox = point.dataLabel.getBBox();
            // Set the y attribute to be just above the column:
            point.dataLabel.attr({ y: point.shapeArgs.y - bbox.height - 2 });
          }
        }
      });
      window.bidirectionalChart.redraw();
    }
  }
}


// ------------------------------------------------------------------------
// Add Event listeners.
// ------------------------------------------------------------------------


// Open Database Dialog
function databaseDialog() {
  window.api.send('open-database-dialog', "Sent.");
}

// Create Deconvoluted Plots when receiving this data
window.api.receive('return-decon-blob-data', (data) => {
  if(data.error) {
    console.error("Error while processing blob data in main process:", data.error);
    return;
  }
  const xicPairs = data.xicArray;
  const atdPairs = data.atdArray;
  const PreXicPairs = data.PreXicArray;
  const PreAtdPairs = data.PreAtdArray;
  displayDeconPlots(xicPairs, atdPairs, PreXicPairs, PreAtdPairs);
});


// Create Deconvoluted Table when receiving this data

window.api.receive('database-table-data', (data, isMapping, error, filepath) => {
  const tableContainer = document.getElementById('deconvoluted-frags-table');
  const errorMessageElement = document.getElementById('error-message');
  const plotsElement = document.getElementById('plots-container');
  const tableMainContainer = document.getElementById('main-table-container');
  if (error) {
      // Hide the table in case of an error
      tableMainContainer.style.border = "none";  
      tableContainer.style.display = "none";
      plotsElement.style.display = "none";
      if (error === "No IDs provided") {
          // Specific message for missing ID values
          errorMessageElement.textContent = 'No deconvoluted DIA fragments found for feature.';
      } else {
          // General error handling
          const errorMsg = `Error fetching data from the database: ${filepath.split("/").pop()}: ${error}`;
          errorMessageElement.textContent = errorMsg;
          console.error(errorMsg);
          console.log("Calling showDeconTable.")
          showDeconTable(data);
      }
      return;
  }
  // If no error, proceed with displaying the data
  tableContainer.style.display = "block";
  errorMessageElement.textContent = '';
  plotsElement.style.display = "block";
  
  if (isMapping) {
      showDeconTable(data);
  } else {
    // This is where the main table is initially started up.
      showMainTable(data);  
  }
});


window.api.receive('raw-blob-result', (data) => {
  if (data.error) {
    console.error(`Error fetching blob (${data.rawType}):`, data.error);
    return;
  }
  if (!data.data) return;

  // For precursor raw data, store it in global variables.
  if (data.rawType === 'DIA_PRE_XIC') {
    window.precursorXICData = data.data;
  } else if (data.rawType === 'DIA_PRE_ATD') {
    window.precursorATDData = data.data;
  }

  // Compute (x,y) pairs if available.
  let pairs = null;
  if (data.data.x && data.data.y) {
    pairs = data.data.x.map((val, i) => [val, data.data.y[i]]);
  } else if (data.rawType === 'DIA_PRE_MS1' && data.data.ms1Array) {
    // Fallback if the raw data for MS1 is provided as ms1Array.
    pairs = data.data.ms1Array;
  }

  // Use the rawType to call the proper display function.
  switch (data.rawType) {
    case 'DIA_PRE_MS1':
      displayMS1Plot(pairs);
      break;
    case 'DIA_PRE_XIC':
      displayXicPlot(pairs);
      break;
    case 'DIA_PRE_ATD':
      displayATDPlot(pairs);
      break;
    default:
      console.warn("Unknown rawType received:", data.rawType);
  }
});


// Create Annotation Table when receiving this data
window.api.receive('database-annotation-data', (data, isMapping, error, filepath) => {
  const tableContainer = document.getElementById('annotation-table');
  const errorMessageElement = document.getElementById('error-message-annotation');
  if (error) {
      tableContainer.style.display = "none";
      if (error === "No IDs provided") {
          errorMessageElement.textContent = 'failed.';
      } else {
          const errorMsg = `Error fetching data from the database: ${filepath.split("/").pop()}: ${error}`;
          errorMessageElement.textContent = errorMsg;
          console.error(errorMsg);
      }
      return;
  }

  showAnnotationTable(data);
  tableContainer.style.display = "block";
  errorMessageElement.textContent = '';
  window.activeTableElement = document.getElementById('main-table-container');
});


// Create ATD plot when receiving this data
window.api.receive('return-atd-blob-data', (data) => {
  if(data.error) {
    console.error("Error while processing blob data in main process:", data.error);
    return;
  }
  const atdPairs = data.atdArray;
  // Render the plots using the received data
  displayATDPlot(atdPairs);
});

document.addEventListener('DOMContentLoaded', () => {
  window.api.receive('selected-database-path', (result) => {
    filePath = result;
    window.api.send('fetch-database-table', result);
    window.api.send('fetch-annotation-table', result);  
  });
});

// Create XIC plot when receiving this data
window.api.receive('return-xic-blob-data', (data) => {
  if(data.error) {
    console.error("Error while processing blob data in main process:", data.error);
    return;
  }
  const xicPairs = data.xicArray;
  // Render the plots using the received data
  displayXicPlot(xicPairs);
});


window.api.receive('lipid-fragment-details', (data) => {
  if (data.error) {
      console.error("Error fetching lipid fragment details:", data.error);
      return;
  }
  // Save details in a global object keyed by dia_frag_id.
  window.lipidFragmentDetails = window.lipidFragmentDetails || {};
  data.details.forEach(detail => {
      window.lipidFragmentDetails[String(detail.dia_frag_id)] = detail;
  });
  // Also, set the selected lipid fragment (if any details are returned)
  if (data.details.length > 0) {
    window.selectedLipidFragmentID = data.details[0].dia_frag_id;
  } else {
    window.selectedLipidFragmentID = null;
  }
  // Now update the bidirectional chart to reflect the new selection.
  updateSelectedDIAHighlight();
});


window.api.receive('delete-annotated-feature-rows-result', (result) => {
  if (result.success) {
    // Update your annotation table with the new data:
    showAnnotationTable(result.updatedData);
    // Optionally, update any other UI elements.
  } else {
    alert("Deletion failed: " + result.error);
  }
});



window.api.receive('dda-ms2-result', (data) => {
  if (data.error) {
    console.error("Error fetching DDA MS2 data:", data.error);
    return;
  }
  // Store the new DDA MS2 data.
  window.ddaMs2Data = data.data; // Expected: {fmz, fint}
  // Now replot the bidirectional MS2 plot if DIA data is available.
  if (window.diaMs2Data) {
    plotBidirectionalMS2(window.ddaMs2Data, window.diaMs2Data);
  }
});

window.api.receive('dia-ms2-result', (data) => {
  if (data.error) {
    console.error("Error fetching DIA MS2 data:", data.error);
    return;
  }
  // Store the DIA MS2 data
  window.diaMs2Data = data.data; // Expected: {fmz, fint}
  // If DDA data is already available, plot bidirectional.
  if (window.ddaMs2Data) {
    plotBidirectionalMS2(window.ddaMs2Data, window.diaMs2Data);
  }
});


window.api.receive('dda-features-result', (data) => {
  if (data.error) {
    console.error("Error fetching DDA features:", data.error);
    return;
  }
  showDDAFeaturesTable(data.features);
  window.activeTableElement = document.getElementById('main-table-container');
});
