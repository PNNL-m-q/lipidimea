

const selectButtonDDA = document.getElementById('select-button-dda');
const selectButtonDIA = document.getElementById('select-button-dia');
const selectButtonDatabase = document.getElementById('select-button-database');
const fileInputDDA = document.getElementById('dda-file-input');
const fileInputDIA = document.getElementById('dia-file-input');

const fileInputDatabase = document.getElementById('database-file-input');
const DDACheckboxGeneral = document.getElementById("experiment-type-dda-general");
const DIACheckboxGeneral = document.getElementById("experiment-type-dia-general");
const DDACheckboxAdvanced= document.getElementById("experiment-type-dda-advanced");
const DIACheckboxAdvanced = document.getElementById("experiment-type-dia-advanced");

const parametersColumnGeneral = document.getElementById("duo-inputs-column-both-general").getElementsByTagName('p');
const inputsColumnGeneral = document.getElementById("duo-inputs-column-both-general").getElementsByTagName('input');


const parametersColumnAdvanced = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
const inputsColumnAdvanced = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');

const ParamEmptyGeneral = document.getElementById("param-empty-gen");
const ParamEmptyAdvanced= document.getElementById("param-empty-adv");



DDACheckboxGeneral.addEventListener("change", handleCheckboxChange);
DIACheckboxGeneral.addEventListener("change", handleCheckboxChange);
DDACheckboxAdvanced.addEventListener("change", handleCheckboxChange);
DIACheckboxAdvanced.addEventListener("change", handleCheckboxChange);

DDACheckboxGeneral.addEventListener("change", UpdateFileOptions);
DIACheckboxGeneral.addEventListener("change", UpdateFileOptions);
DIACheckboxAdvanced.addEventListener("change", UpdateFileOptions);
DDACheckboxAdvanced.addEventListener("change",UpdateFileOptions);



document.addEventListener('DOMContentLoaded', () => {
  window.api.send('getYamlDataBoth');
});

document.addEventListener('DOMContentLoaded', () => {
  window.api.send('file-content');
});


document.addEventListener('DOMContentLoaded', () => {
  window.api.send('selected-database-path');
});



document.addEventListener('DOMContentLoaded', () => {
  const loadPersonalButton = document.getElementById('load-personal-button-general');
  loadPersonalButton.addEventListener('click', handleLoadPersonalButtonClick);
});

document.addEventListener('DOMContentLoaded', () => {
  const loadPersonalButton = document.getElementById('load-personal-button-advanced');
  loadPersonalButton.addEventListener('click', handleLoadPersonalButtonClick);
});

if (selectButtonDDA) {
  selectButtonDDA.addEventListener('click', () => {
    fileInputDDA.click();
  }
)};

if (selectButtonDIA) {
  selectButtonDIA.addEventListener('click', () => {
    fileInputDIA.click();
  }
)};
  
if (selectButtonDatabase) {
  selectButtonDatabase.addEventListener('click', () => {
    fileInputDatabase.click();
  }
)};

if (fileInputDDA) {
  fileInputDDA.addEventListener('change', () => {
    handleFileSelection(fileInputDDA, fileListDDA, filesDDA);
  });
}

if (fileInputDIA) {
  fileInputDIA.addEventListener('change', () => {
    handleFileSelection(fileInputDIA, fileListDIA, filesDIA);
  });
}

if (fileInputDatabase) {
  fileInputDatabase.addEventListener('change', () => {
    handleFileSelection(fileInputDatabase, fileListDatabase, filesDatabase);
  });
}


// document.getElementById('create-new-option').addEventListener('change', function() {
//   if (this.checked) {
//       document.getElementById('new-db-name-container').style.display = 'block';
//   }
// });

// Hide the input if any other DB option is selected
// document.getElementById('append-option').addEventListener('change', function() {
//   if (this.checked) {
//       document.getElementById('new-db-name-container').style.display = 'none';
//   }
// });
// document.getElementById('overwrite-option').addEventListener('change', function() {
//   if (this.checked) {
//       document.getElementById('new-db-name-container').style.display = 'none';
//   }
// });




// Call the synchronizeCheckboxes function when the page is loaded
document.addEventListener('DOMContentLoaded', synchronizeCheckboxes);





// Tab navigation of Experiment Page
document.addEventListener('DOMContentLoaded', () => {
document.getElementsByClassName('tablinks')[0].click();
});

// Function to switch between tabs
function openTab(evt, tabName) {
  var i, tabcontent, tablinks;

  // Hide all tab content
  tabcontent = document.getElementsByClassName('tabcontent');
  for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = 'none';
  }

  // Remove the "active" class from all tab links
  tablinks = document.getElementsByClassName('tablinks');
  for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(' active', '');
  }

  // Show the current tab and add an "active" class to the button that opened the tab
  document.getElementById(tabName).style.display = 'block';
  evt.currentTarget.className += ' active';
}



// Receive DIA data from Defaults Yaml
// window.api.receive('yamlDataDIA', (data) => {
//   const parametersColumnDIA = document.getElementById('parameters-column-dia');
//   const inputsColumnDIA = document.getElementById('inputs-column-dia');

//   if (data) {
//     const parametersDIA = data.PARAMETERS.DIA;
//     const mainElementNamesDIA = Object.keys(data.PARAMETERS.DIA);

//     const sectionsDIA = [];
//     for (let i = 0; i < mainElementNamesDIA.length; i++) {
//       const display_name = mainElementNamesDIA[i];
//       if (display_name !== 'do_processing') {
//         sectionsDIA.push(display_name);
//       }
//     }

//     sectionsDIA.forEach((sectionDIA) => {
//       const sectionDataDIA = parametersDIA[sectionDIA];
//       const parameterTextDIA = document.createElement('p');
//       const emptyText = document.createElement('p');
//       parameterTextDIA.textContent = sectionDIA;
//       parameterTextDIA.id = sectionDIA;
//       parameterTextDIA.key = 'Ignore';
//       parameterTextDIA.style.fontSize = '20px';
//       parameterTextDIA.style.fontWeight = 'bold';
//       parametersColumnDIA.appendChild(parameterTextDIA);
//       emptyText.style.fontSize = '20px';
//       emptyText.textContent = ''
//       emptyText.key = 'Ignore';
      
//       inputsColumnDIA.appendChild(emptyText)
//       Object.entries(sectionDataDIA).forEach(([key, value]) => {
//         const parameterTextDIA = document.createElement('p');
//         parameterTextDIA.textContent = value.display_name;
//         parameterTextDIA.id = key;
//         parameterTextDIA.title = value.description;
//         parametersColumnDIA.appendChild(parameterTextDIA);
//         const inputDIA = document.createElement('input');
//         inputDIA.type = value.type;
//         inputDIA.value = value.default;
//         inputDIA.id = key;
//         inputsColumnDIA.appendChild(inputDIA);
//       });

//     });

//   } else {
//     console.error('Error loading YAML file');
//   }
// });


// Receive DDA data from Defaults Yaml
// window.api.receive('yamlDataDDA', (data) => {
//   const parametersColumnDDA = document.getElementById('parameters-column-dda');
//   const inputsColumnDDA = document.getElementById('inputs-column-dda');

//   if (data) {
//     const parametersDDA = data.PARAMETERS.DDA;
//     const mainElementNamesDDA = Object.keys(data.PARAMETERS.DDA);

//     const sectionsDDA = [];
//     for (let i = 0; i < mainElementNamesDDA.length; i++) {
//       const display_name = mainElementNamesDDA[i];
//       if (display_name !== 'do_processing') {
//         sectionsDDA.push(display_name);
//       }
//     }

//     sectionsDDA.forEach((sectionDDA) => {
//       const sectionDataDDA = parametersDDA[sectionDDA];
//       const parameterTextDDA = document.createElement('p');
//       const emptyText = document.createElement('p');
//       parameterTextDDA.textContent = sectionDDA;
//       parameterTextDDA.id = sectionDDA;
//       parameterTextDDA.key = 'Ignore';
//       parameterTextDDA.style.fontSize = '20px';
//       parameterTextDDA.style.fontWeight = 'bold';
//       parametersColumnDDA.appendChild(parameterTextDDA);
//       emptyText.style.fontSize = '20px';
//       emptyText.textContent = ''
//       emptyText.key = 'Ignore';
//       inputsColumnDDA.appendChild(emptyText)
//       Object.entries(sectionDataDDA).forEach(([key, value]) => {
//         const parameterTextDDA = document.createElement('p');
//         parameterTextDDA.textContent = value.display_name;
//         parameterTextDDA.id = key;
//         parameterTextDDA.title = value.description;
//         parametersColumnDDA.appendChild(parameterTextDDA);
//         const inputDDA = document.createElement('input');
//         inputDDA.type = value.type;
//         inputDDA.value = value.default;
//         inputDDA.id = key;
//         inputsColumnDDA.appendChild(inputDDA);
//       });

//     });

//   } else {
//     console.error('Error loading YAML file');
//   }
// });



// #Before:
// Receive DDA-DIA data from Defaults Yaml
let loadyamlonce = true;
window.api.receive('yamlDataBoth', (data) => {
  data = { PARAMETERS: data };
  // console.log("loadyamlonce:",loadyamlonce)
  if (loadyamlonce === true) {
    loadyamlonce = false
  
  if (data) {
    const parametersBoth = { ...data.PARAMETERS.dda, ...data.PARAMETERS.dia };
    const parametersTop = { ...data.PARAMETERS };
    const mainElementTop = Object.keys(data.PARAMETERS);

    const sectionsTopBoth = mainElementTop.filter(display_name => display_name !== 'misc');

    // const parametersColumnBothAdvanced = document.getElementById('parameters-column-both-advanced');
    // const inputsColumnBothAdvanced = document.getElementById('inputs-column-both-advanced');
    const duoinputsColumnBothGeneral = document.getElementById('duo-inputs-column-both-general');
    const duoinputsColumnBothAdvanced = document.getElementById('duo-inputs-column-both-advanced');
    // const parametersColumnBothGeneral = document.getElementById('parameters-column-both-general');
    // const inputsColumnBothGeneral = document.getElementById('inputs-column-both-general');

    sectionsTopBoth.forEach((sectionTopBoth) => {
      const sectionsBoth = Object.keys(parametersTop[sectionTopBoth]).filter(key => key !== "misc");
    
      const parameterTextBothAdvanced = document.createElement('p');
      parameterTextBothAdvanced.textContent = sectionTopBoth;
      parameterTextBothAdvanced.style.justifyContent= 'left';
      parameterTextBothAdvanced.style.fontSize = '24px';
      parameterTextBothAdvanced.style.fontWeight = 'bold';
      parameterTextBothAdvanced.id = sectionTopBoth;
      parameterTextBothAdvanced.style.gridColumn = '1';
      // parameterTextBothAdvanced.class = 'parameters-column-both-advanced'

      // parameterTextBothAdvanced.style.border = '1px solid #940707';
      // parameterTextBothAdvanced.style.textAlign = 'right';
      parameterTextBothAdvanced.style.gridColumn = 'span 2';
      parameterTextBothAdvanced.key = 'Ignore'; // Assign 'Ignore' to key property
      duoinputsColumnBothAdvanced.appendChild(parameterTextBothAdvanced);
      const emptyTextAdvanced = document.createElement('input');
      emptyTextAdvanced.style.fontSize = '24px';
      emptyTextAdvanced.textContent = '';
      emptyTextAdvanced.key = 'Ignore';
      emptyTextAdvanced.style.gridColumn = '2';
      emptyTextAdvanced.style.display = 'none';
      // emptyTextAdvanced.class = 'inputs-column-both-advanced'
      // emptyTextAdvanced.style.border = '1px solid #940707';
      duoinputsColumnBothAdvanced.appendChild(emptyTextAdvanced);
    
      const parameterTextBothGeneral = document.createElement('p');
      parameterTextBothGeneral.textContent = sectionTopBoth;
      // parameterTextBothGeneral.style.justifyContent= 'right';
      parameterTextBothGeneral.style.fontSize = '24px';
      parameterTextBothGeneral.style.fontWeight = 'bold';
      // parameterTextBothGeneral.style.textAlign = 'right';
      parameterTextBothGeneral.id = sectionTopBoth;
      parameterTextBothGeneral.style.gridColumn = '1';
      // parameterTextBothGeneral.style.border = '1px solid #940707';
      parameterTextBothGeneral.style.gridColumn = 'span 2';
      // parameterTextBothGeneral.style.display = 'none';
      parameterTextBothGeneral.key = 'Ignore'; // Assign 'Ignore' to key property
      // parameterTextBothGeneral.class = 'parameters-column-both-general'
      duoinputsColumnBothGeneral.appendChild(parameterTextBothGeneral);
      const emptyTextGeneral = document.createElement('input');
      emptyTextGeneral.style.fontSize = '24px';
      emptyTextGeneral.textContent = '';
      emptyTextGeneral.key = 'Ignore';
      emptyTextGeneral.style.display='none';
      emptyTextGeneral.style.gridColumn = '2';
      // emptyTextGeneral.class = 'inputs-column-both-general'
      // emptyTextGeneral.style.border = '1px solid #940707';
      duoinputsColumnBothGeneral.appendChild(emptyTextGeneral);
    
      sectionsBoth.forEach((sectionBoth) => {
        const sectionDataBoth = parametersBoth[sectionBoth];
        const generalValues = Object.entries(sectionDataBoth).filter(([key, value]) => !value.advanced);
        const advancedValues = Object.entries(sectionDataBoth);

        
        if (advancedValues.length > 0 ) {
        const parameterTextBothAdvanced = document.createElement('p');
        parameterTextBothAdvanced.textContent = sectionBoth;
        parameterTextBothAdvanced.style.fontSize = '24px';
        parameterTextBothAdvanced.style.fontSize = '20px';
        parameterTextBothAdvanced.style.fontWeight = 'bold';
        // parameterTextBothAdvanced.style.justifyContent= 'right';
        // parameterTextBothAdvanced.style.textAlign = 'right';
        parameterTextBothAdvanced.id = sectionBoth;
        parameterTextBothAdvanced.style.gridColumn = '1';
        // parameterTextBothGeneral.class = 'parameters-column-both-advanced'
        // parameterTextBothAdvanced.style.border = '1px solid #940707';
        parameterTextBothAdvanced.style.gridColumn = 'span 2';
        parameterTextBothAdvanced.key = 'Ignore'; // Assign 'Ignore' to key property
        duoinputsColumnBothAdvanced.appendChild(parameterTextBothAdvanced);
        const emptyTextAdvanced = document.createElement('input');
        emptyTextAdvanced.style.fontSize = '20px';
        emptyTextAdvanced.style.display = 'none';
        emptyTextAdvanced.textContent = '';
        emptyTextAdvanced.key = 'Ignore';

        emptyTextAdvanced.style.gridColumn = '2';
        // emptyTextAdvanced = 'inputs-column-both-advanced'
        // emptyTextAdvanced.style.border = '1px solid #940707';
        duoinputsColumnBothAdvanced.appendChild(emptyTextAdvanced);
        };

        if (generalValues.length > 0 ) {
        const parameterTextBothGeneral = document.createElement('p');
        parameterTextBothGeneral.textContent = sectionBoth;
        parameterTextBothGeneral.style.fontWeight = 'bold';
        // parameterTextBothGeneral.style.textAlign = 'right';
        parameterTextBothGeneral.style.fontSize = '20px';
        parameterTextBothGeneral.style.fontWeight = 'bold';
        parameterTextBothGeneral.id = sectionBoth;
        parameterTextBothGeneral.style.gridColumn = '1';
        // parameterTextBothGeneral.class = 'parameters-column-both-advanced'
        // parameterTextBothGeneral.style.border = '1px solid #940707';
        parameterTextBothGeneral.style.gridColumn = 'span 2';
        parameterTextBothGeneral.key = 'Ignore'; // Assign 'Ignore' to key property
        duoinputsColumnBothGeneral.appendChild(parameterTextBothGeneral);
        const emptyTextGeneral = document.createElement('input');
        emptyTextGeneral.style.fontSize = '20px';
        emptyTextGeneral.style.display = 'none';
        emptyTextGeneral.textContent = '';
        emptyTextGeneral.key = 'Ignore';

        emptyTextGeneral.style.gridColumn = '2';
        // emptyTextGeneral.class = 'inputs-column-both-general'
        // emptyTextGeneral.style.border = '1px solid #940707';
        duoinputsColumnBothGeneral.appendChild(emptyTextGeneral);
        };
        
        // Only include values with "advanced" set to false in the "general" section
        // const generalValues = Object.entries(sectionDataBoth).filter(([key, value]) => !value.advanced);

        generalValues.forEach(([key, value]) => {
          const parameterTextBothGeneral = document.createElement('p');
          parameterTextBothGeneral.textContent = value.display_name;
          parameterTextBothGeneral.id = key;
          parameterTextBothGeneral.title = value.description;
          parameterTextBothGeneral.style.gridColumn = '1';
          // parameterTextBothGeneral.class = 'parameters-column-both-general'
          // parameterTextBothGeneral.style.border = '1px solid #940707';
          // parameterTextBothGeneral.key = 'Ignore'; // Assign 'Ignore' to key property
          duoinputsColumnBothGeneral.appendChild(parameterTextBothGeneral);

          const inputBothGeneral = document.createElement('input');
          inputBothGeneral.type = value.type;
          inputBothGeneral.value = value.default;
          inputBothGeneral.id = key;
          inputBothGeneral.style.gridColumn = '2';
          // inputBothGeneral.class = 'inputs-column-both-general'
          // inputBothGeneral.style.border = '1px solid #940707';
          duoinputsColumnBothGeneral.appendChild(inputBothGeneral);

          // Event listener for changes in the 'general parameters' tab
          inputBothGeneral.addEventListener('change', (event) => {
            const updatedValue = event.target.value;
            const correspondingInputAdvanced = document.getElementById('duo-inputs-column-both-advanced');        
            const oldInputs = Array.from(correspondingInputAdvanced.getElementsByTagName('input'));
            const index = oldInputs.findIndex((input) => input.id === event.target.id);
          
            if (index !== -1) {
              oldInputs[index].value = updatedValue;
            }
          });
        });

        advancedValues.forEach(([key, value]) => {
          const parameterTextBothAdvanced = document.createElement('p');
          parameterTextBothAdvanced.textContent = value.display_name;
          parameterTextBothAdvanced.id = key;
          parameterTextBothAdvanced.title = value.description;
          parameterTextBothAdvanced.style.gridColumn = '1';
          // parameterTextBothAdvanced.class = 'parameters-column-both-advanced'
          // parameterTextBothAdvanced.style.border = '1px solid #940707';
          // parameterTextBothAdvanced.key = 'Ignore'; // Assign 'Ignore' to key property
          duoinputsColumnBothAdvanced.appendChild(parameterTextBothAdvanced);
          // inputsColumnBothAdvanced.appendChild(parameterTextBothAdvanced);


          const inputBothAdvanced = document.createElement('input');
          inputBothAdvanced.type = value.type;
          inputBothAdvanced.value = value.default;
          inputBothAdvanced.id = key;
          inputBothAdvanced.style.gridColumn = '2';
          // inputBothAdvanced.class = 'inputs-column-both-advanced'
          // inputBothAdvanced.style.border = '1px solid #940707';
          duoinputsColumnBothAdvanced.appendChild(inputBothAdvanced);
          // inputsColumnBothAdvanced.appendChild(inputBothAdvanced);


          // Event listener for changes in the 'advanced parameters' tab
          inputBothAdvanced.addEventListener('change', (event) => {
            const updatedValue = event.target.value;
            const correspondingInputGeneral = document.getElementById('duo-inputs-column-both-general');
            const oldInputs = Array.from(correspondingInputGeneral.getElementsByTagName('input'));
            const index = oldInputs.findIndex((input) => input.id === event.target.id);

            if (index !== -1) {
              oldInputs[index].value = updatedValue;
            }
          });
        });
      });
    });
  }}
});

// After:
// window.api.receive('yamlDataBoth', (data) => {
//   if (!data) return;

//   const duoinputsColumnBothGeneral = document.getElementById('duo-inputs-column-both-general');
//   const duoinputsColumnBothAdvanced = document.getElementById('duo-inputs-column-both-advanced');

//   // Loop over both DDA and DIA
//   ['DDA', 'DIA'].forEach(method => {
//       const methodData = data.PARAMETERS[method];
//       for (const sectionTopKey in methodData) {
//           createUIElements(sectionTopKey, methodData[sectionTopKey], duoinputsColumnBothGeneral, 'general');
//           createUIElements(sectionTopKey, methodData[sectionTopKey], duoinputsColumnBothAdvanced, 'advanced');
//       }
//   });
// });

// function createUIElements(sectionKey, sectionData, parentElement, type) {
//   // Create top section element
//   const topSectionElement = document.createElement('p');
//   topSectionElement.textContent = sectionKey;
//   topSectionElement.style.fontSize = '24px';
//   topSectionElement.style.fontWeight = 'bold';
//   topSectionElement.style.gridColumn = 'span 2';
//   parentElement.appendChild(topSectionElement);

//   const emptyText = document.createElement('input');
//   emptyText.style.fontSize = '24px';
//   emptyText.style.display = 'none';
//   parentElement.appendChild(emptyText);

//   for (const parameterKey in sectionData) {
//       const parameterValue = sectionData[parameterKey];

//       if (type === 'general' && parameterValue.advanced) continue; // Skip parameters that are advanced only

//       const parameterElement = document.createElement('p');
//       parameterElement.textContent = parameterKey;
//       parameterElement.id = parameterKey;
//       parameterElement.style.fontSize = '20px';
//       parameterElement.style.gridColumn = '1';
//       parentElement.appendChild(parameterElement);

//       const inputElement = document.createElement('input');
//       inputElement.type = 'text'; // Assuming text, but you might need to adjust this based on your data
//       inputElement.value = parameterValue; // Assuming the value is the direct value, adjust if needed
//       inputElement.id = parameterKey;
//       inputElement.style.gridColumn = '2';
//       parentElement.appendChild(inputElement);
//   }
// }




// Enhancement
// To DO: Add in another parameter that is the file name and possibly file save location.
// To do: ignore hidden parameters (.style.display = "none")
// Possible update, remove hardcoded DDA / DIA.
// function WriteToYaml(i) {
//   const inputValues = {};
//   // const inputs = document.getElementById(i)[1];
//   // const inputs2 = document.getElementById(i)[0];
//   const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
//   const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');
//   console.log("A")
//   console.log(inputs)
//   console.log("B")
//   console.log(inputs2)
//   let ticker = 0
  
//   for (let i = 0; i < inputs.length; i++) {
//     const input = inputs[i];
//     console.log(i," C: ",input)
//     let input2 = inputs2[i];
//     // console.log("input1:", input, input.id,input.key)
//     // console.log("input2:",input2, input2.id, input2.key)

//     if (input2.id === "DDA" || input2.id === "DIA") {
//       ticker++;
//       input2 = inputs2[i];

//     }
//     if (input2 && input2.key === "Ignore") {
//       ticker++;
//       input2 = inputs2[i];
//     }
    
//     if (input && input2) {
//       // console.log(input2, input2.key);
//       if (input.style.display != "none") {
//       inputValues[input2.id] = input.value;
//       };
//     }
//   }
  
//   const options = {
//     pythonPath: 'python3',
//     args: inputValues,
//   };

//   // console.log('Options:', options);
//   window.api.send('run-python-yamlwriter', options);
// }



function WriteToYaml(i) {
  const inputValues = {};
  const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
  const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');

  let currentHeader = null;
  let currentSubheader = null;

  for (let i = 0; i < inputs.length; i++) {
    const input = inputs[i];
    let input2 = inputs2[i];

    // Detect if the element represents a header
    if (input2.id === "dda" || input2.id === "dia") {
      currentHeader = input2.id;
      inputValues[currentHeader] = {};
      currentSubheader = null;  // Reset subheader when a new header is detected
      continue;
    }

    // Detect if the element represents a subheader
    if (input2 && input2.key === "Ignore") {
      currentSubheader = input2.id;
      inputValues[currentHeader][currentSubheader] = {};  // Initialize a sub dictionary for the subheader
      continue;
    }

    // If we're within a header and subheader, nest the input values accordingly
    if (input && input2 && input.style.display != "none") {
      if (currentHeader && currentSubheader) {
        inputValues[currentHeader][currentSubheader][input2.id] = input.value;
      } else if (currentHeader) {
        inputValues[currentHeader][input2.id] = input.value;
      } else {
        inputValues[input2.id] = input.value;
      }
    }
  }

  const options = {
    pythonPath: 'python3',
    args: inputValues,
  };

  window.api.send('run-python-yamlwriter', options);
}





function handleLoadPersonalButtonClick() {
  window.api.send('open-file-dialog', {
    filters: [{ name: 'YAML Files', extensions: ['yaml', 'yml'] }],
    properties: ['openFile'],
  });
}

// Currently Working Again
// function populateInputsFromYaml(yamlData) {
//   const keyValuePairs = Object.entries(yamlData);

//   let inputsColumn;
//   inputsColumn = document.getElementById('duo-inputs-column-both-advanced');
//   let old_inputs = Array.from(inputsColumn.getElementsByTagName('input'));
//   for (let i = 0; i < old_inputs.length; i++) {
//     const oldInput = old_inputs[i];
//     for (let j = 0; j < keyValuePairs.length; j++) {
//       const [key, value] = keyValuePairs[j];
//       if (key === oldInput.id) {
//         oldInput.value = value;
//         break;
//       }
//     }
//   }

//   inputsColumn = document.getElementById('duo-inputs-column-both-general');
//   old_inputs = Array.from(inputsColumn.getElementsByTagName('input'));
//   for (let i = 0; i < old_inputs.length; i++) {
//     const oldInput = old_inputs[i];
//     for (let j = 0; j < keyValuePairs.length; j++) {
//       const [key, value] = keyValuePairs[j];
//       if (key === oldInput.id) {
//         oldInput.value = value;
//         break;
//       }
//     }
//   }

// }

function populateInputsFromYaml(yamlData) {
  // Helper function to set input values based on keys in the data
  function setInputValues(inputElements, data) {
      for (let i = 0; i < inputElements.length; i++) {
          const inputElem = inputElements[i];
          const value = data[inputElem.id];
          if (value !== undefined) {
              inputElem.value = value;
          }
      }
  }

  // Function to flatten the nested structure into a single object
  function flattenYamlData(data) {
      let flatData = {};
      for (const [key, value] of Object.entries(data)) {
          if (typeof value === 'object') {
              flatData = {...flatData, ...flattenYamlData(value)};
          } else {
              flatData[key] = value;
          }
      }
      return flatData;
  }

  const flattenedData = flattenYamlData(yamlData);

  let inputsColumn;
  inputsColumn = document.getElementById('duo-inputs-column-both-advanced');
  setInputValues(Array.from(inputsColumn.getElementsByTagName('input')), flattenedData);

  inputsColumn = document.getElementById('duo-inputs-column-both-general');
  setInputValues(Array.from(inputsColumn.getElementsByTagName('input')), flattenedData);
}



window.api.receive('file-content', (fileContent) => {
  populateInputsFromYaml(fileContent);
});

window.api.receive('file-dialog-selection', (filePath) => {
  window.api.send('file-dialog-selection', filePath);
});


// window.api.receive('selected-database-path', (fileContent) => {
//   console.log("ooga booga", fileContent)
//   // populateInputsFromYaml(fileContent);
// });

document.addEventListener('DOMContentLoaded', () => {
  // Add event listener after the file is selected
  window.api.receive('selected-database-path', (filePath) => {
    console.log("LOG: renderer.js selected-database-path", filePath);
    // Perform any additional logic with the selected file path
    // For example, you can send the file path to the main process to fetch data from the database
    window.api.send('fetch-database-table', filePath);
  });
});



// Upload Files Section
// const selectButton = document.getElementById('select-button');
const fileListDDA = document.getElementById('file-list-dda');
const fileListDIA = document.getElementById('file-list-dia');
const fileListDatabase = document.getElementById('file-list-database');
const filesDDA = [];
const filesDIA = [];
const filesDatabase= [];


function handleFileSelection(fileInput, fileList, filesArray) {
  const selectedFiles = Array.from(fileInput.files);

  if (fileList.id === 'file-list-database') {
    // Clear the filesArray and the fileList content only for 'file-list-database'
    filesArray.length = 0;
    fileList.innerHTML = '';
  }

  selectedFiles.forEach((file) => {
    filesArray.push(file);
    const listItem = document.createElement('li');
    const removeButton = document.createElement('button');
    removeButton.classList.add('remove-button');
    removeButton.innerHTML = '\u274C';
    removeButton.addEventListener('click', () => {
      filesArray.splice(
        filesArray.findIndex((f) => f.name === file.name),
        1
      );
      listItem.remove();
    });

    listItem.innerHTML = `
      <span class="file-text" data-path="${file.path}">${file.name}</span>
    `;
    listItem.appendChild(removeButton);
    fileList.appendChild(listItem);
  });

  fileInput.value = null; // Reset file input
}




// THis whole section is a mess... 

// Synchronize checkbox states between tabs
function synchronizeCheckboxes() {
  const checkboxesTab1 = document.querySelectorAll('#file-upload input[name="experiment-type"]');
  const checkboxesTab2 = document.querySelectorAll('#parameter-general input[name="experiment-type"]');
  const checkboxesTab3 = document.querySelectorAll('#parameter-advanced input[name="experiment-type"]');
  const checkboxesTab4 = document.querySelectorAll('#run-experiment input[name="experiment-type"]');
  
  // Add event listeners to checkboxes in tab 1
  checkboxesTab1.forEach((checkbox, index) => {
    checkbox.addEventListener('click', function() {
      checkboxesTab2[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
    checkbox.addEventListener('click', function() {
      checkboxesTab3[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
    checkbox.addEventListener('click', function() {
      checkboxesTab4[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
  });

  // Add event listeners to checkboxes in tab 2
  checkboxesTab2.forEach((checkbox, index) => {
    checkbox.addEventListener('click', function() {
      checkboxesTab1[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
    checkbox.addEventListener('click', function() {
      checkboxesTab3[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
    checkbox.addEventListener('click', function() {
      checkboxesTab4[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
  });

  checkboxesTab3.forEach((checkbox, index) => {
    checkbox.addEventListener('click', function() {
      checkboxesTab1[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
    checkbox.addEventListener('click', function() {
      checkboxesTab2[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
    checkbox.addEventListener('click', function() {
      checkboxesTab4[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
  });

  checkboxesTab4.forEach((checkbox, index) => {
    checkbox.addEventListener('click', function() {
      checkboxesTab1[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
    checkbox.addEventListener('click', function() {
      checkboxesTab2[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
    checkbox.addEventListener('click', function() {
      checkboxesTab3[index].checked = checkbox.checked;
      handleCheckboxChange();
    });
  });
}


// Function to handle checkbox change
function handleCheckboxChange() {

  if (DDACheckboxGeneral.checked && DIACheckboxGeneral.checked) {
    showAllSections(parametersColumnGeneral, inputsColumnGeneral,ParamEmptyGeneral);
    showAllSections(parametersColumnAdvanced, inputsColumnAdvanced,ParamEmptyAdvanced);
  } else if (!DDACheckboxGeneral.checked && DIACheckboxGeneral.checked) {
    hideDDASection(parametersColumnGeneral,inputsColumnGeneral,ParamEmptyGeneral);
    hideDDASection(parametersColumnAdvanced, inputsColumnAdvanced,ParamEmptyAdvanced);
  } else if (DDACheckboxGeneral.checked && !DIACheckboxGeneral.checked) {
    hideDIASection(parametersColumnGeneral,inputsColumnGeneral,ParamEmptyGeneral);
    hideDIASection(parametersColumnAdvanced, inputsColumnAdvanced,ParamEmptyAdvanced);
  } else {
    hideAllSections(parametersColumnGeneral,inputsColumnGeneral,ParamEmptyGeneral);
    hideAllSections(parametersColumnAdvanced, inputsColumnAdvanced,ParamEmptyAdvanced);
  }
}

// Function to show all sections
function showAllSections(parametersColumn, inputsColumn,paramEmpty) {

  Array.from(parametersColumn).forEach((element) => {
    element.style.display = "block";
  });
  Array.from(inputsColumn).forEach((element) => {
    if (element.key !== "Ignore") {
    element.style.display = "block";
    }
  });
  paramEmpty.style.display = "none";
}


function hideDDASection(parametersColumn,inputsColumn,paramEmpty) {
  showAllSections(parametersColumn, inputsColumn, paramEmpty);
    key = ["dda", "dia"]
    occurrence = 0
    const parameterElements = Array.from(parametersColumn);
    const inputElements = (inputsColumn);

    console.log("startX")
    console.log(parameterElements)
    console.log(inputElements)
    console.log("endX")


    const targetIndex = parameterElements.findIndex(
      (element) => element.textContent === key[0]
    );
    // parameterElements[0]
    
    if (targetIndex !== -1) {
      parameterElements[targetIndex].style.display = "none";
      inputElements[targetIndex].style.display = "none";

      let count = 0;
      for (let i = targetIndex + 1; i < parameterElements.length; i++) {
        // console.log(parameterElements[i].textContent)
        if (parameterElements[i].textContent === key[0]) {
          count++;
          if (count > occurrence) {
            break;
          }
        }
        if (parameterElements[i].textContent === key[1]) {
          break;
        }
        // console.log("param",parameterElements)
        parameterElements[i].style.display = "none";
        inputElements[i].style.display = "none";

        console.log("start")
        console.log(parameterElements[i])
        console.log(inputElements[i])
        console.log("end")
      }};
    paramEmpty.style.display = "none";
  }


    function hideDIASection(parametersColumn,inputsColumn,paramEmpty) {
      showAllSections(parametersColumn, inputsColumn, paramEmpty);
      key = ["dia", "dda"]
      occurrence = 0
      const parameterElements = Array.from(parametersColumn);
      const inputElements = Array.from(inputsColumn);
  
      const targetIndex = parameterElements.findIndex(
        (element) => element.textContent === key[0]
      );
      
      if (targetIndex !== -1) {
        parameterElements[targetIndex].style.display = "none";
        inputElements[targetIndex].style.display = "none";
  
        let count = 0;
        for (let i = targetIndex + 1; i < parameterElements.length; i++) {
          // console.log(parameterElements[i].textContent)
          if (parameterElements[i].textContent === key[0]) {
            count++;
            if (count > occurrence) {
              break;
            }
          }
          if (parameterElements[i].textContent === key[1]) {
            break;
          }
          parameterElements[i].style.display = "none";
          inputElements[i].style.display = "none";
        }};
      paramEmpty.style.display = "none";
}


// Function to hide all sections
function hideAllSections(parametersColumn, inputsColumn,paramEmpty) {
  Array.from(parametersColumn).forEach((element) => {
    element.style.display = "none";
  });
  Array.from(inputsColumn).forEach((element) => {
    element.style.display = "none";
  });
  paramEmpty.style.display = "flex";
}

// Update file upload options when clicking checkbox in file upload tab.
document.addEventListener('DOMContentLoaded', function() {
  let fileUploadSection = document.getElementById('file-upload');
  console.log("File Upload Section:", fileUploadSection);

  fileUploadSection.addEventListener('change', function(event) {
    let target = event.target;
    // let DDACheckboxAdvanced = document.getElementById('experiment-type-dda-advanced');
    // let diaCheckbox = document.getElementById('experiment-type-dia-advanced');
    // let ddaCheckbox = document.getElementById('experiment-type-dda-general');
    // let diaCheckbox = document.getElementById('experiment-type-dia-general');
    let ddaFileSection = document.getElementById('dda-file-region');
    let diaFileSection = document.getElementById('dia-file-region');

    if (target.id === 'experiment-type-dda-advanced') {
      toggleFileSection(DDACheckboxAdvanced, ddaFileSection);
    } else if (target.id === 'experiment-type-dia-advanced') {
      toggleFileSection(DIACheckboxAdvanced, diaFileSection);
    } else if  (target.id === 'experiment-type-dda-general') {
      toggleFileSection(DDACheckboxGeneral, ddaFileSection);
    } else if (target.id === 'experiment-type-dia-general') {
      toggleFileSection(DIACheckboxGeneral, diaFileSection);
    }

  });

  function toggleFileSection(checkbox, fileSection) {
    if (checkbox.checked) {
      fileSection.style.display = 'block';
    } else {
      fileSection.style.display = 'none';
    }
  }
  
});

// Update file upload options when opening file upload tab. (to match other checkbox clicks on other tabs)

// This breaks other functions... now seems to be working
function UpdateFileOptions() {
  let ddaFileRegion = document.getElementById("dda-file-region");
  let diaFileRegion = document.getElementById("dia-file-region");
  console.log("DIA:",DDACheckboxAdvanced.checked,DIACheckboxAdvanced.checked )
  console.log("DDA:",DDACheckboxAdvanced.checked,DDACheckboxGeneral.checked )
  if (DDACheckboxAdvanced.checked) {
    ddaFileRegion.style.display = "block";
  } else {
    ddaFileRegion.style.display = "none";
  }
  if (DIACheckboxAdvanced.checked) {
    diaFileRegion.style.display = "block";
  } else {
    diaFileRegion.style.display = "none";
  };
  if (DDACheckboxGeneral.checked) {
    diaFileRegion.style.display = "block";
  } else {
    diaFileRegion.style.display = "none";
  };
  if (DIACheckboxGeneral.checked) {
    diaFileRegion.style.display = "block";
  } else {
    diaFileRegion.style.display = "none";
  };
};



const outputBox = document.getElementById('output-box');


function scrollToBottom(element) {
  element.scrollTo({
    top: element.scrollHeight,
    behavior: 'smooth',
    block: 'end',
  });
}


// function RunExperiment() {
//   const inputValues = {};
//   const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');
//   const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
// // const inputsColumnAdvanced = document.querySelectorAll('[style*="grid-column: 2"]');


//   const filesDDA = fileListToArray(fileListDDA);
//   const filesDIA = fileListToArray(fileListDIA);
//   const filesDatabase = fileListToArray(fileListDatabase);
  
//   let ticker = 0;

//   for (let i = 0; i < inputs.length; i++) {
//     const input = inputs[i];
//     let input2 = inputs2[i];
//     console.log("Input 1: ", input)
//     console.log("Input 2: ", input2)
//     if (input2 === 'DDA' || input2 === 'DIA') {
//       // ticker++;
//       input2 = inputs2[i];
//     }
//     if (input2 && input2.key === 'Ignore') {
//       // ticker++;
//       input2 = inputs2[i];
//     }

//     if (input && input2) {
//       if (input.style.display !== 'none') {
//         inputValues[input2.id] = input.value;
//       }
//     }
//   }

//   inputValues['dda_data_files'] = JSON.stringify(getFilePaths(filesDDA));
//   inputValues['dia_data_files'] = JSON.stringify(getFilePaths(filesDIA));
//   inputValues['df_data_files'] = JSON.stringify(getFilePaths(filesDatabase));

//   console.log("Three:",filesDDA,filesDIA,filesDatabase)
//   const options = {
//     pythonPath: 'python3',
//     args: inputValues,
//   };

//   window.api.send('run-python-experiment', options);
// }

// function RunExperiment() {
//   const parameters = {
//     DDA: {},
//     DIA: {},
//     MISC: {}
//   };
  
//   const inputOutput = {
//     dda_data_files: [],
//     dia_data_files: [],
//     lipid_ids_db: []
//   };

//   const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');
//   const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');

//   console.log(DDACheckboxGeneral.checked)
//   console.log(DIACheckboxGeneral.checked)

//   const filesDDA = fileListToArray(fileListDDA);
//   const filesDIA = fileListToArray(fileListDIA);
//   const filesDatabase = fileListToArray(fileListDatabase);

//   let currentHeader = null;
//   let currentSubheader = null;

//   for (let i = 0; i < inputs.length; i++) {
//     const input = inputs[i];
//     let input2 = inputs2[i];

//     if (input2.id === "DDA" || input2.id === "DIA") {
//       currentHeader = input2.id;
//       continue;
//     }
    
//     if (input2.key === 'Ignore') {
//       currentSubheader = input2.id;
//       if (currentHeader && !parameters[currentHeader][currentSubheader]) {
//         parameters[currentHeader][currentSubheader] = {};
//       }
//       continue;
//     }

//     if (input && input2 && input.style.display !== 'none') {
//       if (currentHeader && currentSubheader) {
//         parameters[currentHeader][currentSubheader][input2.id] = input.value;
//       } else if (currentHeader) {
//         parameters[currentHeader][input2.id] = input.value;
//       } else {
//         parameters['MISC'][input2.id] = input.value;
//       }
//     }
//   }

//   inputOutput['dda_data_files'] = filesDDA;
//   inputOutput['dia_data_files'] = filesDIA;
//   inputOutput['lipid_ids_db'] = filesDatabase[0];  // Assuming there's only one file for Database

//   const options = {
//     pythonPath: 'python3',
//     args: {
//       INPUT_OUTPUT: inputOutput,
//       PARAMETERS: parameters
//     }
//   };

//   window.api.send('run-python-experiment', options);
// } 



function getSelectedDatabaseOption() {
  let radios = document.querySelectorAll('.section-container input[name="db_option"]');
  
  for (let radio of radios) {
      if (radio.checked) {
          return radio.value;
      }
  }
}





function RunExperiment() {
  // const parameters = {
  //   dda: {
  //     do_processing: false // Setting the default value to false.
  //   },
  //   dia: {
  //     do_processing: false, // Setting the default value to false.
  //     MISC: {
  //       store_blobs: true
  //     }
  //   },
  //   MISC: {
  //     debug: false
  //   }
  // };

  const parameters = {
      dda: {},
      dia: {},
      misc: {
        dia_store_blobs: true,
        do_dda_processing: false,
        do_dia_processing: false
      }
    };
  // const parameters = {}
  
  const inputOutput = {
    dda_data_files: [],
    dia_data_files: [],
    lipid_ids_db: []
  };

  const selectedDatabaseOption = getSelectedDatabaseOption()
  const selectedDatabaseName = document.getElementById("experiment-name").value
  const selectedSaveLocation = document.getElementById("selected-directory").value

  console.log("1:",selectedDatabaseOption)
  console.log("2:", selectedDatabaseName)
  console.log("3:", selectedSaveLocation)


  const gui_params = {
    db_pick: selectedDatabaseOption,
    db_name: selectedDatabaseName,
    save_loc: selectedSaveLocation
  }

  const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');
  const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');

  console.log(DDACheckboxGeneral.checked)
  console.log(DIACheckboxGeneral.checked)

  if (DDACheckboxGeneral.checked === true) {
    parameters.misc.do_dda_processing = true;
  }
  
  if (DIACheckboxGeneral.checked === true) {
    parameters.misc.do_dia_processing = true;
  }

  const filesDDA = fileListToArray(fileListDDA);
  const filesDIA = fileListToArray(fileListDIA);
  const filesDatabase = fileListToArray(fileListDatabase);

  let currentHeader = null;
  let currentSubheader = null;

  for (let i = 0; i < inputs.length; i++) {
    const input = inputs[i];
    let input2 = inputs2[i];
    console.log("A",input2)

    if (input2.id === "dda" || input2.id === "dia") {
      currentHeader = input2.id;
      console.log("B/Current Header",input2.id)
      continue;
    }
    
    if (input2.key === 'Ignore') {
      currentSubheader = input2.id;
      if (currentHeader && !parameters[currentHeader][currentSubheader]) {
        parameters[currentHeader][currentSubheader] = {};
      }
      continue;
    }

    if (input && input2 && input.style.display !== 'none') {
      if (currentHeader && currentSubheader) {
        parameters[currentHeader][currentSubheader][input2.id] = input.value;
      } else if (currentHeader) {
        parameters[currentHeader][input2.id] = input.value;
      } else {
        parameters['misc'][input2.id] = input.value;
      }
    }
  }

  inputOutput['dda_data_files'] = filesDDA;
  inputOutput['dia_data_files'] = filesDIA;
  inputOutput['lipid_ids_db'] = filesDatabase[0];  // Assuming there's only one file for Database


  console.log("LOOK HERE:")
  console.log(gui_params)
  const options = {
    pythonPath: 'python3',
    args: {
      input_output: inputOutput,
      params: parameters,
      options: gui_params
    }
  };

  window.api.send('run-python-experiment', options);
} 





window.api.receive('python-result-experiment', (result) => {
  console.log('Received result:', result);
  outputBox.innerText += result + '\n'; // Append the result to the output box
  scrollToBottom(outputBox);
});


// function fileListToArray(fileList) {
//   return Array.from(fileList.getElementsByTagName('li')).map((listItem) => {
//     const fileText = listItem.querySelector('.file-text');
//     console.log("fileText:",fileText)
//     return {
//       name: fileText.textContent,
//       path: fileText.dataset.path,
//     };
//   });
// }

function fileListToArray(fileList) {
  return Array.from(fileList.getElementsByTagName('li')).map((listItem) => {
    const fileText = listItem.querySelector('.file-text');
    console.log("fileText:",fileText);
    // Return only the path for each file
    return fileText.dataset.path;
  });
}

function getFilePaths(filesArray) {
  console.log("filesArray:",filesArray.map((file) => file.path))
  return filesArray.map((file) => file.path);
}


function displayFileName(input) {
  const selectedFileNameElement = document.getElementById('selectedFileName');
  if (input.files.length > 0) {
    selectedFileNameElement.textContent = input.files[0].name;
  } else {
    selectedFileNameElement.textContent = '';
  }
}


function databaseDialog() {
  window.api.send('open-database-dialog',"Sent.");
}



document.addEventListener('DOMContentLoaded', () => {
  console.log("LOG: renderer.js DOMContentLoaded");

  window.api.receive('selected-database-path', (result) => {
    console.log("LOG: renderer.js selected-database-path", result);
    window.api.send('fetch-database-table', result);
  });
});


// Listen for the database table data from the main process
window.api.receive('database-table-data', (data) => {
  // Display the fetched data in a table on the results.html page
  // You can modify this code to format and display the data as desired
  console.log("yay")
  const tableContainer = document.getElementById('table-container');
  tableContainer.innerHTML = ''; // Clear previous table content

  const table = document.createElement('table');
  const thead = document.createElement('thead');
  const tbody = document.createElement('tbody');

  // Add table headers
  const headers = Object.keys(data[0]);
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
      td.textContent = row[header];
      tableRow.appendChild(td);
    });
    tbody.appendChild(tableRow);
  });

  table.appendChild(thead);
  table.appendChild(tbody);
  tableContainer.appendChild(table);
});




function selectSaveDirectory() {
  window.api.send('open-directory-dialog');
}

window.api.receive('directory-selected', (path) => {
  console.log("Selected directory:", path);
  document.getElementById('selected-directory').value = path;
});
