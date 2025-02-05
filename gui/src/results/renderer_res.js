// Declare Variables

let filePath = null;
let selectedRowValue = null;
let isMappingTable = false;
let lastSelectedRowValue = null;
let mzRowMap = new Map();
let DeconTableMzSet;
const DeconTable_MATCH_COLOR = '#E6A7B2';

// ------ Event Listeners and Receivers ----------

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
  const xicDistVal = document.getElementById('xic-dist-value');
  const atdDistVal = document.getElementById('atd-dist-value');
  const plotsElement = document.getElementById('plots-container');
  const tableMainContainer = document.getElementById('main-table-container');
  if (error) {
      // Hide the table in case of an error
      tableMainContainer.style.border = "none";
      tableContainer.style.display = "none";
      xicDistVal.style.display = "none";
      atdDistVal.style.display = "none";
      plotsElement.style.display = "none";
      if (error === "No IDs provided") {
          // Specific message for missing ID values
          errorMessageElement.textContent = 'No deconvoluted DIA fragments found for feature.';
      } else {
          // General error handling
          const errorMsg = `Error fetching data from the database: ${filepath.split("/").pop()}: ${error}`;
          errorMessageElement.textContent = errorMsg;
          console.error(errorMsg);
          showDeconTable(data);
      }
      return;
  }
  // If no error, proceed with displaying the data
  tableContainer.style.display = "block";
  errorMessageElement.textContent = '';
  xicDistVal.style.display = "block";
  atdDistVal.style.display = "block";
  plotsElement.style.display = "block";
  
  if (isMapping) {
      showDeconTable(data);
  } else {
      showMainTable(data);
  }
});


// Create MS1 plot when receving this data
window.api.receive('return-ms1-blob-data', (data) => {
  if(data.error) {
    console.error("Error while processing blob data in main process:", data.error);
    return;
  }
  const ms1Pairs = data.ms1Array;
  displayMS1Plot(ms1Pairs);
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


// TODO: CALL THIS SOMETHING
document.addEventListener('DOMContentLoaded', () => {
  window.api.receive('selected-database-path', (result) => {
    //filePath = result;
    window.api.send('fetch-database-table', result);
    window.api.send('fetch-annotation-table', result);
    // load all the rest of the elements
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



// ------ Helper Functions ----------



// Format Decimals to 4 Places. This allows many values to be mapped across tables / plots.
function formatDecimalValue(value) {
  if (typeof value === 'number' && !Number.isInteger(value)) {
    return value.toFixed(4);
  }
  return value;
}

// Parse Peak Data
function parsePeaks(dataString) {
  return dataString.split(' ').map(peak => {
    const [mz, intensity] = peak.split(':');
    return {
      mz: parseFloat(mz),
      intensity: parseFloat(intensity)
    };
  });
}


// Called in Annotation Table. Select mapped rows in Main Table
function findInMainTableByFeatureId(featureId) {
  const mainTableContainer = document.getElementById('main-table-container');
  const rows = mainTableContainer.querySelectorAll('tr');
  rows.forEach(row => {
      // Assuming the feature ID is in the third column
      const featureIdCell = row.children[2];
      if (featureIdCell && parseInt(featureIdCell.textContent, 10) === featureId) {
        row.dispatchEvent(new Event('click', { 'bubbles': true }));  
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
  });
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

// Called in Mapped Feature Table. Select mapped rows in Main Table
function highlightRowInMainTable(diaFeatureId) {
  const mainTable = document.getElementById('main-table-container');
  const rows = mainTable.querySelectorAll('tbody tr'); 
  rows.forEach(row => {
      const featureIdCell = row.cells[2]; // Get the third cell 
      if (String(featureIdCell.textContent) === String(diaFeatureId)) {
        row.click();
      }
  });
}

// Function get a set of all m/z values from DeconTable
function getDeconTableMzSet() {
  const DeconTableMzValues = Array.from(document.querySelectorAll('#deconvoluted-frags-table tbody tr td:first-child')).map(td => parseFloat(td.innerText).toFixed(4));
  return new Set(DeconTableMzValues);
}

// Set DIA color of columns. (Plots)
function getDIAColor(mzValue, DeconTableMzSet) {
  const existsInDeconTable = DeconTableMzSet.has(mzValue.toFixed(4));
  if (existsInDeconTable) {
      return DeconTable_MATCH_COLOR;  
  } else {
      return '#7cb5ec'; 
  }
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

  // Validate the conversion and input values
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

  // When selecting a different a row in the Decon Table, update Decon Plots.
function processDeconRowData(row) {
    const mzValueElement = document.getElementById('atd-dist-value');
    const rtValueElement = document.getElementById('xic-dist-value');
    mzValueElement.textContent = "XIC Distance: " + formatDecimalValue(row['xic_dist']);
    rtValueElement.textContent = "ATD Distance: " + formatDecimalValue(row['atd_dist']);

    window.api.send('process-decon-blob-data', {
      dia_xic: row['xic'],
      dia_atd: row['atd'],
      pre_dia_xic: row['dia_xic'],
      pre_dia_atd: row['dia_atd']
    });
}


// ------ Table Creation Functions ----------


// Create Main Table
function showMainTable(data) {
  const tableContainer = document.getElementById('main-table-container');
  tableContainer.innerHTML = ''; 
  tableContainer.style.border = "1px solid black";
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');

  // Add table headers
  const headers = Object.keys(data[0]).filter(header => 
  header !== "dia_decon_frag_ids" 
  && header !== "dia_xic"
  && header !== "dia_atd"
  && header !== "dia_dt" 
  && header !== "dia_dt_pkht" 
  && header !== "dia_dt_fwhm" 
  && header !== "dia_rt_pkht"
  && header !== "dia_rt_fwhm"
  && header !== "dia_rt_psnr"
  && header !== "dda_rt_pkht"
  && header !== "dda_rt_fwhm"
  && header !== "dda_rt_psnr"
  && header !== "dda_rt"
  && header !== "dda_ms2_peaks"
  && header !== "dia_ms2_peaks"
  && header !== "dia_dt_fwhm" 
  && header !== "dia_dt_fwhm" 
  && header !== "dia_dt_fwhm" 
  && header !== "dia_dt_fwhm" 
  && header !== "dia_dt_fwhm" 
  && header !== "dia_dt_psnr"
  && header !== "dia_ms1");
  const headerRow = document.createElement('tr');
  headers.forEach((header) => {
      const th = document.createElement('th');
      th.textContent = header;
      headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  // Add table rows
  data.forEach((row) => {
      const tableRow = document.createElement('tr');
      headers.forEach((header) => {
          const td = document.createElement('td');
          td.textContent = formatDecimalValue(row[header]);
          tableRow.appendChild(td);
      });

      const id = row[headers[2]]; // Assuming the DIA Feature ID column is the identifier

      // Add click event listener to each row
      tableRow.addEventListener('click', () => {
          // Remove previous selection if any
          const previousSelectedRow = tbody.querySelector('.selected');
          if (previousSelectedRow) {
              previousSelectedRow.classList.remove('selected');
          }

          // Set the current row as selected
          tableRow.classList.add('selected');

          selectedRowValue = {
              id: id,
              diaDeconFragIds: row['dia_decon_frag_ids']
          };

          const mzValueElement = document.getElementById('mz-value');
          const DIArtValueElement = document.getElementById('dia-rt-value');
          const dtValueElement = document.getElementById('dia-dt-value');
          const DTpkhtValueElement = document.getElementById('dia-dt-pkht-value');
          const DTfwhmValueElement = document.getElementById('dia-dt-fwhm-value');
          const DTpsnrValueElement = document.getElementById('dia-dt-psnr-value');
          const DIArtPKHTValueElement = document.getElementById('dia-rt-pkht-value');
          const DIArtFWHMValueElement = document.getElementById('dia-rt-fwhm-value');
          const DIArtPSNRValueElement = document.getElementById('dia-rt-psnr-value');
          const DDArtValueElement = document.getElementById('dda-rt-value');
          const DDArtPKHTValueElement = document.getElementById('dda-rt-pkht-value');
          const DDArtFWHMValueElement = document.getElementById('dda-rt-fwhm-value');
          const DDArtPSNRValueElement = document.getElementById('dda-rt-psnr-value');
          const PreDIAatdValueElement = document.getElementById('dia-atd-value');
          const PreDIAxicValueElement = document.getElementById('dia-xic-value');

          mzValueElement.textContent = formatDecimalValue(row['m/z']);
          DIArtValueElement.textContent = formatDecimalValue(row['RT']);
          dtValueElement.textContent = formatDecimalValue(row['dia_dt']);
          DTpkhtValueElement.textContent = formatDecimalValue(row['dia_dt_pkht']);
          DTfwhmValueElement.textContent = formatDecimalValue(row['dia_dt_fwhm']);
          DTpsnrValueElement.textContent = formatDecimalValue(row['dia_dt_psnr']);
          DIArtPKHTValueElement.textContent = formatDecimalValue(row['dia_rt_pkht']);
          DIArtFWHMValueElement.textContent = formatDecimalValue(row['dia_rt_fwhm']);
          DIArtPSNRValueElement.textContent = formatDecimalValue(row['dia_rt_psnr']);
          DDArtValueElement.textContent = formatDecimalValue(row['dda_rt']);
          DDArtPKHTValueElement.textContent = formatDecimalValue(row['dda_rt_pkht']);
          DDArtFWHMValueElement.textContent = formatDecimalValue(row['dda_rt_fwhm']);
          DDArtPSNRValueElement.textContent = formatDecimalValue(row['dda_rt_psnr']);
          PreDIAatdValueElement.textContent = row['dia_xic'];
          PreDIAxicValueElement.textContent = row['dia_atd'];

          window.api.send('fetch-mapping-table', selectedRowValue);

          // TODO: Fetch blob data for the selected DIA feature ID from index.js
          //        Process blob data can just fetch the blob data from database (based on feat ID)
          //        then process and return it.

          window.api.send('process-xic-blob-data', {
            dia_xic: row['dia_xic']
          });

          window.api.send('process-atd-blob-data', {
            dia_atd: row['dia_atd']
          });

          window.api.send('process-ms1-blob-data', {
            dia_ms1: row['dia_ms1']
          });


          showMappedFeatureTable(data,row['DDA Feature ID']);
          console.log("error now")
          console.log(row['dda_ms2_peaks'])
          console.log(row['dia_ms2_peaks'])          
          if (row['dda_ms2_peaks'] !== null || row['dia_ms2_peaks'] !== null) {
            const ddaData = parsePeaks(row['dda_ms2_peaks'])
            const diaData = parsePeaks(row['dia_ms2_peaks'])

            // This a patch fix. If time, find better fix.
            // Race conditions make it so this is rendered before DeconTable
            // So the delay allows DeconTable to be generated first.
            setTimeout(() => {
              document.getElementById("bidirectional-plot").style.display = "flex";
              document.getElementById('error-message-bidirectional-plot').style.display = "none";
              plotBidirectionalColumn(ddaData, diaData);
            }, 200);
          }
          else { 
            document.getElementById("bidirectional-plot").style.display = "none";
            document.getElementById('error-message-bidirectional-plot').style.display = "flex";
          }

            const resultsDisplay = document.getElementById('below-table-content');
            resultsDisplay.style.display = 'block';

        const diaFeatureIdColumn = row['DIA Feature ID'];
          if (diaFeatureIdColumn !== undefined) {
              findInAnnTableByFeatureId(diaFeatureIdColumn);
          }
        
      });

      // Add hover effect to each row
      tableRow.addEventListener('mouseover', () => {
          tableRow.classList.add('hover');
      });

      tableRow.addEventListener('mouseout', () => {
          tableRow.classList.remove('hover');
      });

      tbody.appendChild(tableRow);

  });

  table.appendChild(thead);
  table.appendChild(tbody);
  tableContainer.appendChild(table);
}


// Create Deconvoluted Feature Table
function showDeconTable(data) {
  const tableContainer = document.getElementById('deconvoluted-frags-table');
  tableContainer.innerHTML = ''; // Clear previous content
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');
  // Add table headers
  let mzColumnIndex = -1;
  const headers = ["m/z"];
  const headerRow = document.createElement('tr');
  headers.forEach((header, index) => {
      const th = document.createElement('th');
      th.textContent = header;
      headerRow.appendChild(th);
      if (header === "m/z") {
          mzColumnIndex = index;
      }
  });
  thead.appendChild(headerRow);
  // Create an observer instance for monitoring class changes
  const observer = new MutationObserver((mutationsList, observer) => {
    for(let mutation of mutationsList) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            const tableRow = mutation.target;
            if (tableRow.classList.contains('selected-row')) {
                const mzValue = parseFloat(tableRow.children[mzColumnIndex].textContent);
                const TOLERANCE = 1e-4; 
                const row = data.find(r => Math.abs(r.mz - mzValue) < TOLERANCE);
                  processDeconRowData(row);
              }
          }
      }
  });
  data.forEach((row) => {
      const tableRow = document.createElement('tr');
      const td = document.createElement('td');
      td.textContent = formatDecimalValue(row['mz']);
      tableRow.appendChild(td);
      // Store the row in the map
      mzRowMap.set(parseFloat(row['mz']).toFixed(4), tableRow);
      // Observe the row for class changes
      observer.observe(tableRow, { attributes: true, attributeFilter: ['class'] });
      // Click event to perform actions
      tableRow.addEventListener('click', () => {
          const selectedRows = document.querySelectorAll('.selected-row');
          selectedRows.forEach(row => row.classList.remove('selected-row'));
          tableRow.classList.add('selected-row');
          processDeconRowData(row);
      });
      tbody.appendChild(tableRow);
  });

  if (tbody.childNodes.length > 0) {
    // Automatically select the first row
    tbody.childNodes[0].click();
  }
  table.appendChild(thead);
  table.appendChild(tbody);
  tableContainer.appendChild(table);
}


// Create Mapped Feature Table
function showMappedFeatureTable(data,dda_mapped) {
  const tableContainer = document.getElementById('table-dda-mapped-dia');
  tableContainer.innerHTML = ''; 

  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');

  // Add table headers
  const headers = ['DIA Feature ID', 'DIA Data File'];
  const headerRow = document.createElement('tr');
  headers.forEach((header) => {
      const th = document.createElement('th');
      th.textContent = header;
      headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  // Add table rows
  data.forEach((row) => {
    if (row['DDA Feature ID'] === dda_mapped) {
      const tableRow = document.createElement('tr');
      headers.forEach((header) => {
          const td = document.createElement('td');
          td.textContent = row[header];
          tableRow.appendChild(td);
      });

      tableRow.addEventListener('click', function() {
          // Remove the previous selection if any
          const previousSelectedRow = tbody.querySelector('.selected');
          if (previousSelectedRow) {
              previousSelectedRow.classList.remove('selected');
          }

          // Set the current row as selected
          tableRow.classList.add('selected');

          highlightRowInMainTable(row['DIA Feature ID']);
      });

      // Add hover effect to each row
      tableRow.addEventListener('mouseover', () => {
          tableRow.classList.add('hover');
      });

      tableRow.addEventListener('mouseout', () => {
          tableRow.classList.remove('hover');
      });

      // Add more functionalities as required for each row
      tbody.appendChild(tableRow);
    }
  });

  table.appendChild(thead);
  table.appendChild(tbody);
  tableContainer.appendChild(table);
}

// Create Annotation Table
function showAnnotationTable(data) {
  const tableContainer = document.getElementById('annotation-table');
  tableContainer.innerHTML = ''; 

  if (!data || data.length === 0) {
      console.error("No data provided.");
      return;
  }

  // Sort data based on the 'dia_feat_id' column
  data.sort((a, b) => {
      return a['dia_feat_id'] - b['dia_feat_id'];
  });

  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');

  // Create headers
  const headers = Object.keys(data[0]);
  const headerRow = document.createElement('tr');
  headers.forEach(header => {
      const th = document.createElement('th');
      th.textContent = header;
      headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  // Create rows
  data.forEach(row => {
      const tableRow = document.createElement('tr');

      headers.forEach(header => {
          const td = document.createElement('td');
          td.textContent = row[header];
          tableRow.appendChild(td);
      });

      // Add event listener to make rows selectable
      tableRow.addEventListener('click', function() {
          // Remove selection from previously selected row
          const selectedRow = tableContainer.querySelector('.selected-row');
          if (selectedRow) {
              selectedRow.classList.remove('selected-row');
          }
          // Add selection to the current row
          tableRow.classList.add('selected-row');

          const diaFeatureIdColumn = row['dia_feat_id'];
          if (diaFeatureIdColumn !== undefined) {
              findInMainTableByFeatureId(diaFeatureIdColumn);
          }
      });

      tbody.appendChild(tableRow);
  });

  table.appendChild(thead);
  table.appendChild(tbody);
  tableContainer.appendChild(table);
}



// ------ Plot Generation Functions ----------



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
          document.getElementById('dia-dt-value').textContent,
          document.getElementById('dia-dt-pkht-value').textContent,
          document.getElementById('dia-dt-fwhm-value').textContent
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
Highcharts.chart('ion-chromatogram-plot', {
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
            document.getElementById('dia-rt-value').textContent, 
            document.getElementById('dia-rt-pkht-value').textContent, 
            document.getElementById('dia-rt-fwhm-value').textContent
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
      data: generateGaussianData(
        document.getElementById('dda-rt-value').textContent,
        document.getElementById('dda-rt-pkht-value').textContent,
        document.getElementById('dda-rt-fwhm-value').textContent
        ),
      type: 'line',
      name: 'Fit (DDA)',
      color: '#808080', 
      dashStyle: 'dash',
      marker: {
          enabled: false
      }
  }],
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


// Bi-Directional DDA-DIA Plot Generation
function plotBidirectionalColumn(ddaData, diaData) {
  const combinedMzValues = Array.from(new Set([...ddaData.map(peak => peak.mz), ...diaData.map(peak => peak.mz)])).sort((a, b) => a - b);
  DeconTableMzSet = new Set(
    Array.from(document.querySelectorAll('#deconvoluted-frags-table tbody tr td:first-child'))
    .map(cell => parseFloat(cell.innerText).toFixed(4))
  );
  const labelStep = Math.floor(combinedMzValues.length / 5);
    Highcharts.chart('bidirectional-plot', {
      chart: {
        type: 'column',
        backgroundColor: null,
        zoomType: 'xy',
          panning: true,
          resetZoomButton: {
            position: {
                align: 'left', 
                verticalAlign: 'top', 
                x: 0,
                y: 0
            }}   
    },
    credits: {
        enabled: false  
    },
    title: {
      text: 'DDA & DIA Peaks'
    },
    legend: {
      align: 'right',        
      verticalAlign: 'top',   
      layout: 'vertical',
      floating: true,        
      x: -10,               
      y: -10              
  },
    xAxis: {
      min: Math.min(...combinedMzValues),
      max: Math.max(...combinedMzValues),
      title: {
        text: 'm/z'
      }
    },
    yAxis: [{
      title: {
        text: 'DDA Intensity'
      },
      labels: {
        formatter: function () {
          return Math.abs(this.value);
        }
      },
      top: '50%',
      height: '50%',
      offset: 0,
      lineWidth: 1,
      opposite: false  
    }, {
      title: {
        text: 'DIA Intensity'
      },
      labels: {
        formatter: function () {
          return this.value;
        }
      },
      top: '0%',
      height: '50%',
      offset: 0,
      lineWidth: 1,
      opposite: false 
    }],
    plotOptions: {
      column: {
        pointPadding: 1, 
        borderWidth: 0,   
        groupPadding: 0,  
        shadow: false,
        allowPointSelect: true,
        states: {
          select: {
            color: '#800080'
          }}},
      events: {
        select: function(event) {
          if (event.target.color !== DeconTable_MATCH_COLOR) {
            event.target.select(false, true);
          }
        }},
      series: {
        cursor: 'pointer',
        events: {
          click: function (event) {
            if (this.name === 'DIA' && event.point.color === DeconTable_MATCH_COLOR) {  
              selectDeconTableRow(event.point.category);
            }
          }
        }        
    }
    },
    series: [{
      name: 'DDA',
      yAxis: 0,
      data: ddaData.map(peak => ({
        x: peak.mz, 
        y: -peak.intensity,
        color: "#BFA6BF"
      }))
    }, {
      name: 'DIA',
      yAxis: 1,
      data: diaData.map(peak => ({
        x: peak.mz,  
        y: peak.intensity,
        color: getDIAColor(peak.mz, DeconTableMzSet),
        pointWidth: getDIAWidth(peak.mz, DeconTableMzSet)
      }))
    }]
  });
}




// MS1 Plot Generation
function displayMS1Plot(ms1Pairs) {
  const xValue = parseFloat(document.getElementById('mz-value').textContent);
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
