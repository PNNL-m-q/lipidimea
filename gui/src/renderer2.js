// document.addEventListener("DOMContentLoaded", function() {
//   var table = document.getElementById("table-container");
//   if (table.querySelector("tr")) {
//       table.style.border = "1px solid black";
//   }
// });






function databaseDialog() {
  window.api.send('open-database-dialog', "Sent.");
}

let filePath = null;
let selectedRowValue = null;
let isMappingTable = false;
let lastSelectedRowValue = null;

function formatDecimalValue(value) {
  if (typeof value === 'number' && !Number.isInteger(value)) {
    return value.toFixed(4);
  }
  return value;
}


function showTable1(data) {
  const tableContainer = document.getElementById('table-container');
  tableContainer.innerHTML = ''; // Clear previous table content
  tableContainer.style.border = "1px solid black";
  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');
  // const belowTableContent = document.getElementById('below-table-content');

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
  // && header !== "dda_ms2_peaks"
  // && header !== "dia_ms2_peaks"
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

          const ddaFeatureIdElement = document.getElementById('dda-feature-id');
          const diaFeatureIdElement = document.getElementById('dia-feature-id');
          const mzValueElement = document.getElementById('mz-value');
          const DIArtValueElement = document.getElementById('dia-rt-value');
          const arrivalTimeElement = document.getElementById('arrival-time');
          const dtValueElement = document.getElementById('dia-dt-value');
          const DTpkhtValueElement = document.getElementById('dia-dt-pkht-value');
          const DTfwhmValueElement = document.getElementById('dia-dt-fwhm-value');
          const DTpsnrValueElement = document.getElementById('dia-dt-psnr-value');

          const DIArtValueElement2 = document.getElementById('dia-rt-value-2');
          const DIArtPKHTValueElement = document.getElementById('dia-rt-pkht-value');
          const DIArtFWHMValueElement = document.getElementById('dia-rt-fwhm-value');
          const DIArtPSNRValueElement = document.getElementById('dia-rt-psnr-value');

          const DDArtValueElement = document.getElementById('dda-rt-value');
          const DDArtPKHTValueElement = document.getElementById('dda-rt-pkht-value');
          const DDArtFWHMValueElement = document.getElementById('dda-rt-fwhm-value');
          const DDArtPSNRValueElement = document.getElementById('dda-rt-psnr-value');

          const PreDIAatdValueElement = document.getElementById('dia-atd-value');
          const PreDIAxicValueElement = document.getElementById('dia-xic-value');

          // const DDAPeaksValueElement = document.getElementById('dda-peaks-value');
          // const DIAPeaksValueElement = document.getElementById('dia-peaks-value');


          ddaFeatureIdElement.textContent = row['DDA Feature ID'];
          diaFeatureIdElement.textContent = row['DIA Feature ID'];
          mzValueElement.textContent = formatDecimalValue(row['m/z']);
          DIArtValueElement.textContent = formatDecimalValue(row['RT']);
          arrivalTimeElement.textContent = formatDecimalValue(row['Arrival Time']);
          dtValueElement.textContent = formatDecimalValue(row['dia_dt']);
          DTpkhtValueElement.textContent = formatDecimalValue(row['dia_dt_pkht']);
          DTfwhmValueElement.textContent = formatDecimalValue(row['dia_dt_fwhm']);
          DTpsnrValueElement.textContent = formatDecimalValue(row['dia_dt_psnr']);

          DIArtValueElement2.textContent = formatDecimalValue(row['RT']);
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

          window.api.send('process-blob-data-mid-top', {
            // dia_xic: document.getElementById('dia-xic-value').textContent,
            dia_xic: row['dia_xic']
          });

          window.api.send('process-blob-data-mid-bot', {
            // dia_xic: document.getElementById('dia-xic-value').textContent,
            dia_atd: row['dia_atd']
          });

          window.api.send('process-blob-data-left-top', {
            // dia_xic: document.getElementById('dia-xic-value').textContent,
            dia_ms1: row['dia_ms1']
          });

          // window.api.send('fetch-related-dia-features', row['DDA Feature ID']);
          // console.log("sending dda id: ", row['DDA Feature ID'])
          showTable3(data,row['DDA Feature ID']);
          console.log("error now")
          console.log(row['dda_ms2_peaks'])
          console.log(row['dia_ms2_peaks'])
          // ADD NOTE WHEN NO PEAKS FOUND!
          
          // 
          if (row['dda_ms2_peaks'] !== null || row['dia_ms2_peaks'] !== null) {
            const ddaData = parsePeaks(row['dda_ms2_peaks'])
            const diaData = parsePeaks(row['dia_ms2_peaks'])
          
            // plotBidirectionalColumn(ddaData, diaData);

            // This a patch fix. If time, find better fix.
            // Race conditions make it so this is rendered before table2
            // So the delay allows table2 to be generated first.
            setTimeout(() => {
              plotBidirectionalColumn(ddaData, diaData);
            }, 200);
          }

            const resultsDisplay = document.getElementById('below-table-content');
            resultsDisplay.style.display = 'block';
        
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



  if (isMappingTable) {
      const selectedTableRow = tbody.querySelector(`[data-id="${selectedRowValue.id}"]`);
      if (selectedTableRow) {
          selectedTableRow.classList.add('selected');
      }
  } else if (lastSelectedRowValue) {
      const lastSelectedTableRow = tbody.querySelector(`[data-id="${lastSelectedRowValue.id}"]`);
      if (lastSelectedTableRow) {
          lastSelectedTableRow.classList.add('selected');
          lastSelectedTableRow.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
      }
  }
}

let mzRowMap = new Map();

function showTable2(data) {
  const tableContainer = document.getElementById('second-row-third-box-table');
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
  // console.log('m/z column index:', mzColumnIndex); 
  thead.appendChild(headerRow);

  // Create an observer instance for monitoring class changes
  const observer = new MutationObserver((mutationsList, observer) => {
    for(let mutation of mutationsList) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            const tableRow = mutation.target;
            if (tableRow.classList.contains('selected-row')) {
                const mzValue = parseFloat(tableRow.children[mzColumnIndex].textContent);
                const TOLERANCE = 1e-4;  // Adjust this value as necessary
                const row = data.find(r => Math.abs(r.mz - mzValue) < TOLERANCE);
                  processRowData(row);
              }
          }
      }
  });

  function processRowData(row) {
    const mzValueElement = document.getElementById('atd-dist-value');
    const rtValueElement = document.getElementById('xic-dist-value');

    mzValueElement.textContent = "XIC Distance: " + formatDecimalValue(row['xic_dist']);
    rtValueElement.textContent = "ATD Distance: " + formatDecimalValue(row['atd_dist']);

    window.api.send('process-blob-data', {
      dia_xic: row['xic'],
      dia_atd: row['atd'],
      pre_dia_xic: row['dia_xic'],
      pre_dia_atd: row['dia_atd']
    });
  }

  // Add table rows
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
          // console.log('Proc Row selected',row)
          // selectPlotPeak(parseFloat(row['mz']).toFixed(4),table2MzSet);
          processRowData(row);
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

// function selectPlotPeak(mzValue) {
//     mzValue = parseFloat(mzValue).toFixed(4); 
//     // Find the specific chart by its container's ID
//     const chart = Highcharts.charts.find(ch => ch.renderTo.id === 'first-row-third-box-plot');
//     if (!chart) return;  // Exit if the chart was not found

//     const pointIndex = chart.xAxis[0].categories.map(val => parseFloat(val).toFixed(4)).indexOf(mzValue);

//     if (pointIndex !== -1) {
//         // Deselect and reset visual style for any currently selected peak
//         chart.series[1].data.forEach(point => {
//             point.select(false, false);
//             point.update({
//                 color: getDIAColor(point.category, table2MzSet) // reset to its original color
//             }, false);
//         });

//         // Select the corresponding peak and highlight it
//         const point = chart.series[1].data[pointIndex];
//         point.select(true);
//         point.update({
//             color: '#800080' // highlight color
//         });
//     }

//     // Re-draw the chart to reflect the changes
//     chart.redraw();
// }



function selectTableRow(mzValue) {
  // Find the row for the given m/z value
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


document.addEventListener('DOMContentLoaded', () => {
  window.api.receive('selected-database-path', (result) => {
    filePath = result;
    window.api.send('fetch-database-table', result);
  });
});


function displayFileName(input) {
  const selectedFileName = document.getElementById('selectedFileName');
  selectedFileName.textContent = input.files[0].name;
}


window.api.receive('database-table-data', (data, isMapping, error, filepath) => {
  const tableContainer = document.getElementById('second-row-third-box-table');
  const errorMessageElement = document.getElementById('error-message');
  const xicDistVal = document.getElementById('xic-dist-value');
  const atdDistVal = document.getElementById('atd-dist-value');
  const plotsElement = document.getElementById('plots-container');
  const tableMainContainer = document.getElementById('table-container');
  // If there's an error, handle it
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
          showTable2(data);
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
      showTable2(data);
  } else {
      showTable1(data);
  }
});



function generateGaussianData(mean, height,width) {
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




function displayPlots(xicPairs, atdPairs, PreXicPairs, PreAtdPairs) {

  const normalize = pairs => {
    const maxValue = Math.max(...pairs.map(pair => pair[1]));
    return pairs.map(pair => [pair[0], pair[1] / maxValue]);
  };

// Normalize each set of pairs independently
  xicPairs = normalize(xicPairs);
  atdPairs = normalize(atdPairs);
  PreXicPairs = normalize(PreXicPairs);
  PreAtdPairs = normalize(PreAtdPairs);
  
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
              // padding: '2px 2px' 
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
      align: 'right',         // Horizontally aligns to the right
      verticalAlign: 'top',   // Vertically aligns to the top
      layout: 'vertical',
      floating: true,         // Allows the legend to float/overlap the chart
      x: -10,                 // Optional horizontal offset; negative values shift it to the left
      y: -10                   // Optional vertical offset; positive values shift it down
  },
    credits: {
        enabled: false
    }
};

// XIC Plot
Highcharts.chart('second-row-third-box-xic-plot', {
  // chart: {
  //   width: 300,  // desired width in pixels
  //   height: 150  // desired height in pixels
  // },  
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

// ATD Plot
Highcharts.chart('second-row-third-box-atd-plot', {
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





window.api.receive('processed-4-blob-data', (data) => {
  if(data.error) {
    console.error("Error while processing blob data in main process:", data.error);
    return;
  }

  const xicPairs = data.xicArray;
  const atdPairs = data.atdArray;
  const PreXicPairs = data.PreXicArray;
  const PreAtdPairs = data.PreAtdArray;

  // Render the plots using the received data
  displayPlots(xicPairs, atdPairs, PreXicPairs, PreAtdPairs);
});





function displayMidBotPlot(atdPairs) {
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
      align: 'right',         // Horizontally aligns to the right
      verticalAlign: 'top',   // Vertically aligns to the top
      layout: 'vertical',
      floating: true,         // Allows the legend to float/overlap the chart
      x: -10,                 // Optional horizontal offset; negative values shift it to the left
      y: -10                   // Optional vertical offset; positive values shift it down
  },
    credits: {
        enabled: false
    }
};


Highcharts.chart('second-row-second-box-plot', {
  // chart: {
  //   width: 300,  // desired width in pixels
  //   height: 150  // desired height in pixels
  // },  
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
      data: generateGaussianData(document.getElementById('dia-dt-value').textContent, document.getElementById('dia-dt-pkht-value').textContent, document.getElementById('dia-dt-fwhm-value').textContent),
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



window.api.receive('processed-blob-data-mid-bot', (data) => {
  if(data.error) {
    console.error("Error while processing blob data in main process:", data.error);
    return;
  }

  // const xicPairs = data.xicArray;
  const atdPairs = data.atdArray;
  
  // Render the plots using the received data
  displayMidBotPlot(atdPairs);
});





function displayMidTopPlot(xicPairs) {
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
              // padding: '2px 2px' 
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
      align: 'right',         // Horizontally aligns to the right
      verticalAlign: 'top',   // Vertically aligns to the top
      layout: 'vertical',
      floating: true,         // Allows the legend to float/overlap the chart
      x: -10,                 // Optional horizontal offset; negative values shift it to the left
      y: -10                   // Optional vertical offset; positive values shift it down
  },
    credits: {
        enabled: false
    }
};
Highcharts.chart('first-row-second-box-plot', {
  // chart: {
  //   width: 300,  // desired width in pixels
  //   height: 150  // desired height in pixels
  // },  
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
      data: generateGaussianData(document.getElementById('dia-rt-value').textContent, document.getElementById('dia-rt-pkht-value').textContent, document.getElementById('dia-rt-fwhm-value').textContent),
      type: 'line',
      name: 'Fit (DIA)',
      color: 'black', 
      dashStyle: 'dash',
      marker: {
          enabled: false
      }
  },
  {
      data: generateGaussianData(document.getElementById('dda-rt-value').textContent, document.getElementById('dda-rt-pkht-value').textContent, document.getElementById('dda-rt-fwhm-value').textContent),
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


window.api.receive('processed-blob-data-mid-top', (data) => {
  if(data.error) {
    console.error("Error while processing blob data in main process:", data.error);
    return;
  }

  const xicPairs = data.xicArray;

  // Render the plots using the received data
  displayMidTopPlot(xicPairs);
});



function parsePeaks(dataString) {
  return dataString.split(' ').map(peak => {
    const [mz, intensity] = peak.split(':');
    return {
      mz: parseFloat(mz),
      intensity: parseFloat(intensity)
    };
  });
}




const TABLE2_MATCH_COLOR = '#E6A7B2';
// Optimized function to get a set of all m/z values from table2
function getTable2MzSet() {
  const table2MzValues = Array.from(document.querySelectorAll('#second-row-third-box-table tbody tr td:first-child')).map(td => parseFloat(td.innerText).toFixed(4));
  return new Set(table2MzValues);
}

function getDIAColor(mzValue, table2MzSet) {
  const existsInTable2 = table2MzSet.has(mzValue.toFixed(4));
  if (existsInTable2) {
      return TABLE2_MATCH_COLOR;  
  } else {
      return '#7cb5ec'; 
  }
}

function getDIAWidth(mzValue, table2MzSet) {
  const existsInTable2 = table2MzSet.has(mzValue.toFixed(4));
  if (existsInTable2) {
      return 2;  
  } else {
      return 1; 
  }
}



let table2MzSet;

function plotBidirectionalColumn(ddaData, diaData) {
  const combinedMzValues = Array.from(new Set([...ddaData.map(peak => peak.mz), ...diaData.map(peak => peak.mz)])).sort((a, b) => a - b);
  table2MzSet = new Set(
    Array.from(document.querySelectorAll('#second-row-third-box-table tbody tr td:first-child'))
    .map(cell => parseFloat(cell.innerText).toFixed(4))
);
const labelStep = Math.floor(combinedMzValues.length / 5);
  Highcharts.chart('first-row-third-box-plot', {
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
          }}   // Make chart background transparent
    },
    credits: {
        enabled: false   // Removes the Highcharts watermark/label
    },
    title: {
      text: 'DDA & DIA Peaks'
    },
    legend: {
      align: 'right',         // Horizontally aligns to the right
      verticalAlign: 'top',   // Vertically aligns to the top
      layout: 'vertical',
      floating: true,         // Allows the legend to float/overlap the chart
      x: -10,                 // Optional horizontal offset; negative values shift it to the left
      y: -10                   // Optional vertical offset; positive values shift it down
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
      opposite: false  // This is set to false to move the yAxis to the left
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
      opposite: false  // This is also set to false to move the yAxis to the left
    }],
    plotOptions: {
      column: {
        pointPadding: 1,   // Adjust the padding between columns
        borderWidth: 0,   // Optionally remove the border if desired
        groupPadding: 0,  // Adjust the padding between series/column groups
        shadow: false,
        allowPointSelect: true,
        states: {
          select: {
            color: '#800080'
          }}},
      events: {
        select: function(event) {
          if (event.target.color !== TABLE2_MATCH_COLOR) {
            event.target.select(false, true);
          }
        }},
      series: {
        cursor: 'pointer',
        events: {
          click: function (event) {
            if (this.name === 'DIA' && event.point.color === TABLE2_MATCH_COLOR) {  // And here
              selectTableRow(event.point.category);
            }
          }
        }        
    }
    },
    series: [{
      name: 'DDA',
      yAxis: 0,
      data: ddaData.map(peak => ({
        x: peak.mz,  // Use the actual mz value instead of index
        y: -peak.intensity,
        color: "#BFA6BF"
      }))
    }, {
      name: 'DIA',
      yAxis: 1,
      data: diaData.map(peak => ({
        x: peak.mz,  // Use the actual mz value instead of index
        y: peak.intensity,
        color: getDIAColor(peak.mz, table2MzSet),
        pointWidth: getDIAWidth(peak.mz, table2MzSet)
      }))
    }]
  });
}


function showTable3(data,dda_mapped) {
  const tableContainer = document.getElementById('second-row-first-table-container');
  tableContainer.innerHTML = ''; // Clear previous content

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

          highlightRowInTable1(row['DIA Feature ID']);
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



function highlightRowInTable1(diaFeatureId) {
  const table1 = document.getElementById('table-container');
  const rows = table1.querySelectorAll('tbody tr'); 

  // Loop through rows of table1
  rows.forEach(row => {
      const featureIdCell = row.cells[2]; // Get the third cell 
      if (String(featureIdCell.textContent) === String(diaFeatureId)) {
        row.click();
      }
  });
}






window.api.receive('processed-blob-data-left-top', (data) => {
  if(data.error) {
    console.error("Error while processing blob data in main process:", data.error);
    return;
  }

  // const xicPairs = data.xicArray;
  const ms1Pairs = data.ms1Array;
  
  // Render the plots using the received data
  console.log("lalala")
  displayLeftTopPlot(ms1Pairs);
});


function displayLeftTopPlot(ms1Pairs) {
  const xValue = parseFloat(document.getElementById('mz-value').textContent);
  const maxYValue = ms1Pairs.reduce((max, pair) => Math.max(max, pair[1]), 0);
  // MS1 Plot
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
      align: 'right',         // Horizontally aligns to the right
      verticalAlign: 'top',   // Vertically aligns to the top
      layout: 'vertical',
      floating: true,         // Allows the legend to float/overlap the chart
      x: -10,                 // Optional horizontal offset; negative values shift it to the left
      y: -10                   // Optional vertical offset; positive values shift it down
  },
    credits: {
        enabled: false
    }
};
Highcharts.chart('first-row-first-box-plot', {
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
      dashStyle: 'Dash'  // Make the line dotted
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
      max: maxYValue  // Set the y-axis max value to maxYValue
  }
});
}