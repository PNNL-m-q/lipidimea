

const selectButtonDDA = document.getElementById('select-button-dda');
const selectButtonDIA = document.getElementById('select-button-dia');
const selectButtonDatabase = document.getElementById('select-button-database');
const fileInputDDA = document.getElementById('dda-file-input');
const fileInputDIA = document.getElementById('dia-file-input');

const fileInputDatabase = document.getElementById('database-file-input');

const checkboxes = {
  general: {
      dda: document.getElementById("experiment-type-dda-general"),
      dia: document.getElementById("experiment-type-dia-general"),
      annotate: document.getElementById("experiment-type-annotate-general")
  },
  advanced: {
      dda: document.getElementById("experiment-type-dda-advanced"),
      dia: document.getElementById("experiment-type-dia-advanced"),
      annotate: document.getElementById("experiment-type-annotate-advanced")
  }
};

const parametersColumnGeneral = document.getElementById("duo-inputs-column-both-general").getElementsByTagName('p');
const inputsColumnGeneral = document.getElementById("duo-inputs-column-both-general").getElementsByTagName('input');


const parametersColumnAdvanced = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
const inputsColumnAdvanced = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');

const ParamEmptyGeneral = document.getElementById("param-empty-gen");
const ParamEmptyAdvanced= document.getElementById("param-empty-adv");

const newDB = document.getElementById('db-options');


for (let type in checkboxes) {
  for (let mode in checkboxes[type]) {
      checkboxes[type][mode].addEventListener("change", handleCheckboxChange);
      checkboxes[type][mode].addEventListener("change", UpdateFileOptions);
      // checkboxes[type][mode].addEventListener("change",UpdateAnnotateOptions);
  }
}

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



newDB.addEventListener("change", UpdateExpName);


// const newAn = document.getElementById("experiment-type-annotate-general")
// newAn.addEventListener("change",UpdateAnnotateOptions)

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



function synchronizeCheckboxes() {
  const tabs = [
      '#file-upload',
      '#parameter-general',
      '#parameter-advanced',
      '#run-experiment'
  ];

  tabs.forEach((tab, index) => {
      const checkboxesInCurrentTab = document.querySelectorAll(`${tab} input[name="experiment-type"]`);

      checkboxesInCurrentTab.forEach((checkbox, checkboxIndex) => {
          checkbox.addEventListener('click', function() {
              tabs.forEach((otherTab, otherTabIndex) => {
                  if (index !== otherTabIndex) {
                      const checkboxesInOtherTab = document.querySelectorAll(`${otherTab} input[name="experiment-type"]`);
                      checkboxesInOtherTab[checkboxIndex].checked = checkbox.checked;
                      handleCheckboxChange();
                      UpdateAnnotateOptions();
                  }
              });
          });
      });
  });
}


// Function to handle checkbox change
function handleCheckboxChange() {
  const isDDA = checkboxes.general.dda.checked || checkboxes.advanced.dda.checked;
  const isDIA = checkboxes.general.dia.checked || checkboxes.advanced.dia.checked;
  const isAnnotate = checkboxes.general.annotate.checked || checkboxes.advanced.annotate.checked;


  showAllSections(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
  showAllSections(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  if (isDDA && isDIA && isAnnotate) {
      showAllSections(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      showAllSections(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  } else if (!isDDA && isDIA && isAnnotate) {
      hideDDASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideDDASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  } else if (isDDA && !isDIA && isAnnotate) {
      hideDIASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideDIASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  } else if (isDDA && isDIA && !isAnnotate) {
      hideAnnotateSection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideAnnotateSection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  } else if (isDDA && !isDIA && !isAnnotate) {
      hideDIASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideDIASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
      hideAnnotateSection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideAnnotateSection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  } else if (!isDDA && isDIA && !isAnnotate) {
      hideDDASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideDDASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
      hideAnnotateSection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideAnnotateSection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  } else if (!isDDA && !isDIA && isAnnotate) {
      hideDDASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideDDASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
      hideDIASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideDIASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  // } else {
  //   hideDDASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
  //   hideDDASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  //   hideDIASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
  //   hideDIASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  //   // hideAnnotateSection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
  //   // hideAnnotateSection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  // }
  } else {
      hideAllSections(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideAllSections(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
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
    key = ["dda","dia"]
    occurrence = 0
    const parameterElements = Array.from(parametersColumn);
    const inputElements = (inputsColumn);

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

      }};
    paramEmpty.style.display = "none";
  }


    function hideDIASection(parametersColumn,inputsColumn,paramEmpty) {
      key = ["dia","annotate"]
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

// Change to annotate
function hideAnnotateSection(parametersColumn,inputsColumn,paramEmpty) {
  key = ["annotate","misc"]
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
      toggleFileSection(checkboxes.advanced.dda, ddaFileSection);
    } else if (target.id === 'experiment-type-dia-advanced') {
      toggleFileSection(checkboxes.advanced.dia, diaFileSection);
    } else if  (target.id === 'experiment-type-dda-general') {
      toggleFileSection(checkboxes.general.dda, ddaFileSection);
    } else if (target.id === 'experiment-type-dia-general') {
      toggleFileSection(checkboxes.advanced.dia, diaFileSection);
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


function UpdateFileOptions() {
  const ddaFileRegion = document.getElementById("dda-file-region");
  const diaFileRegion = document.getElementById("dia-file-region");

  ddaFileRegion.style.display = (checkboxes.general.dda.checked || checkboxes.advanced.dda.checked) ? "block" : "none";
  diaFileRegion.style.display = (checkboxes.general.dia.checked || checkboxes.advanced.dia.checked) ? "block" : "none";
}



const outputBox = document.getElementById('output-box');


function scrollToBottom(element) {
  element.scrollTo({
    top: element.scrollHeight,
    behavior: 'smooth',
    block: 'end',
  });
}



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

  console.log(checkboxes.advanced.dda.checked)
  console.log(checkboxes.advanced.dia.checked)

  if (checkboxes.advanced.dda.checked === true) {
    parameters.misc.do_dda_processing = true;
  }
  
  if (checkboxes.advanced.dia.checked === true) {
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


function UpdateExpName() {
  const TF = document.getElementById("create-new-option").checked
  if (TF === true) {
    document.getElementById("new-db-name-container").style.display = "flex"
    document.getElementById("selected-directory-container").style.display = "none"
  }
  else {
    document.getElementById("new-db-name-container").style.display = "none"
    document.getElementById("selected-directory-container").style.display = "flex"
  }
}

function UpdateAnnotateOptions() {
  const TF = checkboxes.general.annotate.checked
  console.log("TF: ", TF)

  if (TF === true) {
    document.getElementById("annotate-options").style.display = "flex"
  }
  else {
    document.getElementById("annotate-options").style.display = "none"
  }
}

