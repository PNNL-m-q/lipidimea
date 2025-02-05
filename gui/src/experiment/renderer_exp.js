
// Declare All Variables
// This includes:
// - Button elements
// - Checkbox elements
// - Radiobutton elements
// - FilePaths
// - param/input elements

// Matching Parameters may exist across File Upload, General, Advanced, Experiment Tabs

// Buttons for file selection
const selectButtonDDA = document.getElementById('select-button-dda');
const selectButtonDIA = document.getElementById('select-button-dia');
const selectButtonDatabase = document.getElementById('select-button-database');
const selectButtonAnnotation = document.getElementById('select-button-annotation');
const fileInputDDA = document.getElementById('dda-file-input');
const fileInputDIA = document.getElementById('dia-file-input');
const fileInputDatabase = document.getElementById('database-file-input');
const fileInputAnnotation = document.getElementById('annotation-file-input');

// Checkboxes
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
// Parameters and inputs
const parametersColumnGeneral = document.getElementById("duo-inputs-column-both-general").getElementsByTagName('p');
const inputsColumnGeneral = document.getElementById("duo-inputs-column-both-general").getElementsByTagName('input');
const parametersColumnAdvanced = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
const inputsColumnAdvanced = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');
const ParamEmptyGeneral = document.getElementById("param-empty-gen");
const ParamEmptyAdvanced= document.getElementById("param-empty-adv");
const databaseOptions = document.getElementById('db-options');
const saveParamsOptions = document.getElementById('save-params');



//  Files Section
const fileListDDA = document.getElementById('file-list-dda');
const fileListDIA = document.getElementById('file-list-dia');
const fileListDatabase = document.getElementById('file-list-database');
const fileListAnnotation = document.getElementById('file-list-annotation');
const filesDDA = [];
const filesDIA = [];
const filesDatabase= [];
const filesAnnotation= [];

// Python Experiment Results Box
const outputBox = document.getElementById('output-box');


// Add Event listeners. DOM triggers immediately

// Checkbox eventlisteners
for (let type in checkboxes) {
  for (let mode in checkboxes[type]) {
      checkboxes[type][mode].addEventListener("change", handleCheckboxChange);
      checkboxes[type][mode].addEventListener("change", UpdateFileOptions);
  }
}
document.addEventListener('DOMContentLoaded', () => {
  window.api.send('getDefaults');
});

// Listener for uploading params 
document.addEventListener('DOMContentLoaded', () => {
  const uploadDataButton = document.getElementById('upload-data-button-general');
  uploadDataButton.addEventListener('click', handleuploadDataButtonClick);
});

// Listener for uploading params 
document.addEventListener('DOMContentLoaded', () => {
  const uploadDataButton = document.getElementById('upload-data-button-advanced');
  uploadDataButton.addEventListener('click', handleuploadDataButtonClick);
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
  
if (selectButtonAnnotation) {
  selectButtonAnnotation.addEventListener('click', () => {
    fileInputAnnotation.click();
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

if (fileInputAnnotation) {
  fileInputAnnotation.addEventListener('change', () => {
    handleFileSelection(fileInputAnnotation, fileListAnnotation, filesAnnotation);
  });
}

databaseOptions.addEventListener("change", UpdateExpName);
saveParamsOptions.addEventListener("change", UpdateExpName);

// Call the synchronizeCheckboxes function when the page is loaded
document.addEventListener('DOMContentLoaded', synchronizeCheckboxes);

// Tab navigation of Experiment Page
document.addEventListener('DOMContentLoaded', () => {
document.getElementsByClassName('tablinks')[0].click();
});

// Function to switch between tabs
function openTab(evt, tabName) {
  console.log(tabName);

  let tabcontent, tablinks;

  // Hide all tab content
  tabcontent = document.getElementsByClassName('tabcontent');
  for (let i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = 'none';
  }

  // Remove the "active" class from all tab links
  tablinks = document.getElementsByClassName('tablinks-sel');
  for (let i = 0; i < tablinks.length; i++) {
      tablinks[i].className = 'tablinks';
  }

  // Show the current tab and add an "active" class to the button that opened the tab
  document.getElementById(tabName).style.display = 'block';
  evt.currentTarget.className = 'tablinks-sel';
}


// Synchronize Checkboxes across tabs whenever they change
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
                      UpdateDatabaseOptions();
                  }
              });
          });
      });
  });
}


// Load Default Params. Create Related Elements.
let loadyamlonce = true;
window.api.receive('returnDefaults', (data) => {
    data = { PARAMETERS: data };

    if (loadyamlonce === true) {
        loadyamlonce = false;

        if (data) {
            const parametersBoth = { ...data.PARAMETERS.dda, ...data.PARAMETERS.dia, ...data.PARAMETERS.annotation };
            const mainElementTop = Object.keys(data.PARAMETERS);
            const sectionsTopBoth = mainElementTop.filter(display_name => display_name !== 'misc');

            const duoinputsColumnBothGeneral = document.getElementById('duo-inputs-column-both-general');
            const duoinputsColumnBothAdvanced = document.getElementById('duo-inputs-column-both-advanced');

            sectionsTopBoth.forEach((sectionTopBoth) => {

                // TODO: Text formatting, some of the keys/values from the YAML are ugly
                const sectionsBoth = Object.keys(data.PARAMETERS[sectionTopBoth]).filter(key => key !== "misc" && key !== "display_name");

                createHeaderElement(data.PARAMETERS[sectionTopBoth].display_name, duoinputsColumnBothAdvanced, sectionTopBoth);
                createHeaderElement(data.PARAMETERS[sectionTopBoth].display_name, duoinputsColumnBothGeneral, sectionTopBoth);

                sectionsBoth.forEach((sectionBoth) => {
                    const sectionDataBoth = parametersBoth[sectionBoth];
                    const generalValues = Object.entries(sectionDataBoth).filter(([key, value]) => !value.advanced && key !== "display_name");
                    const allValues = Object.entries(sectionDataBoth).filter(([key]) => key !== "display_name");

                    if (generalValues.length > 0) {
                        createSubHeaderElement(sectionDataBoth.display_name, duoinputsColumnBothGeneral,sectionBoth);

                        generalValues.forEach(([key, value]) => {
                            createParameterElement(value.display_name, key, value.description, duoinputsColumnBothGeneral);
                            createInput(value.type, value.default, key, duoinputsColumnBothGeneral, duoinputsColumnBothAdvanced);
                        });
                    }

                    if (allValues.length > 0) {
                        createSubHeaderElement(sectionDataBoth.display_name, duoinputsColumnBothAdvanced,sectionBoth);

                        allValues.forEach(([key, value]) => {
                            createParameterElement(value.display_name, key, value.description, duoinputsColumnBothAdvanced);
                            createInput(value.type, value.default, key, duoinputsColumnBothAdvanced, duoinputsColumnBothGeneral);
                        });
                    }
                });
            });
        }
    }
});
// A series of functions to create the param elements
// Ideally style should be formatted in css.
// Note to self - fix this if time.
function createHeaderElement(textContent, parentNode,ID) {
  const element = document.createElement('p');
  element.textContent = textContent;
  element.style.justifyContent = 'left';
  element.style.fontSize = '24px';
  element.style.fontWeight = 'bold';
  element.style.gridColumn = 'span 2';
  element.id = ID;
  element.key = 'Ignore'; // Assign 'Ignore' to key property
  parentNode.appendChild(element);

  createHiddenInput(parentNode);  // Add hidden input for headers
}

function createSubHeaderElement(textContent, parentNode, ID) {
  const element = document.createElement('p');
  element.textContent = textContent;
  element.id = ID;
  element.style.fontSize = '20px';
  element.style.fontWeight = 'bold';
  element.style.gridColumn = 'span 2';
  element.key = 'Ignore'; // Assign 'Ignore' to key property
  parentNode.appendChild(element);

  createHiddenInput(parentNode);  // Add hidden input for subheaders
}

function createHiddenInput(parentNode) {
  const inputElement = document.createElement('input');
  inputElement.type = 'hidden';  // The type is set to 'hidden' to hide the input
  parentNode.appendChild(inputElement);
}

function createParameterElement(textContent, id, title, parentNode) {
    const element = document.createElement('p');
    element.textContent = textContent;
    element.id = id;
    element.title = title;
    element.style.gridColumn = '1';
    parentNode.appendChild(element);
}

function createInput(type, value, id, parentNode, otherTab) {
    const inputElement = document.createElement('input');
    inputElement.type = type;
    inputElement.value = value;
    inputElement.id = id;
    inputElement.style.gridColumn = '2';
    inputElement.key = 'Ignore'; // Assign 'Ignore' to key property

    inputElement.addEventListener('change', (event) => {
        const updatedValue = event.target.value;
        const oldInputs = Array.from(otherTab.getElementsByTagName('input'));
        const index = oldInputs.findIndex((input) => input.id === event.target.id);

        if (index !== -1) {
            oldInputs[index].value = updatedValue;
        }
    });

    parentNode.appendChild(inputElement);
}


// Write User Updated Parameter Values to file
function WriteToYaml(i,name,location) {
  const inputValues = {};
  const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
  const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');

  let currentHeader = null;
  let currentSubheader = null;
  for (let i = 0; i < inputs.length; i++) {
    const input = inputs[i];
    let input2 = inputs2[i];

    // Detect if the element represents a header
    if (input2.id === "dda" || input2.id === "dia" || input2.id === "annotation") {
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

  if (location === undefined || name === undefined){
  const options = {
    pythonPath: 'python3',
    args: inputValues,
  };
  window.api.send('request-filename-and-directory');

  window.api.receive('selected-param-save-directory', (savePath) => {
    const options = {
        pythonPath: 'python3',
        args: inputValues,
        path: savePath
    };
    window.api.send('run-python-yamlwriter', options);
  });
}
else {
  const options = {
    pythonPath: 'python3',
    args: inputValues,
    name: name,
    location: location
};
  window.api.send('run-python-yamlwriter', options);

}

}

// Receive filepath to update parameter values from personal file
window.api.receive('file-dialog-selection', (filePath) => {
  window.api.send('file-dialog-selection', filePath);
});

// Receive data to update parameter values 
window.api.receive('file-content', (fileContent) => {
  populateInputsFromYaml(fileContent);
});


// Load Parameter Values from personal file.
function handleuploadDataButtonClick() {
  window.api.send('open-file-dialog', {
    filters: [{ name: 'YAML Files', extensions: ['yaml', 'yml'] }],
    properties: ['openFile'],
  });
}

// Change param values to match inputs
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

  // Helper function to flatten the nested structure into a single object
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


// File Upload Section
function handleFileSelection(fileInput, fileList, filesArray) {
  const selectedFiles = Array.from(fileInput.files);

  if (fileList.id === 'file-list-database' || fileList.id === 'file-list-annotation') {
    // Clear the filesArray and the fileList content only for 'file-list-database' and 'file-list-annotation'
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


// Function to handle checkbox change
// Hide / Unhide appropriate sections
// These sections have a bit of hard coding...
function handleCheckboxChange() {
  const isDDA = checkboxes.general.dda.checked || checkboxes.advanced.dda.checked;
  const isDIA = checkboxes.general.dia.checked || checkboxes.advanced.dia.checked;
  const isAnnotate = checkboxes.general.annotate.checked || checkboxes.advanced.annotate.checked;

  showAllSections(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
  showAllSections(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
    if (!isDDA) {
      hideDDASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
      hideDDASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  } 
  if (!isDIA) {
    hideDIASection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
    hideDIASection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  } 
  if (!isAnnotate) {
    hideAnnotateSection(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
    hideAnnotateSection(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  }
  if (!isDDA && !isDIA && !isAnnotate) {
    hideAllSections(parametersColumnGeneral, inputsColumnGeneral, ParamEmptyGeneral);
    hideAllSections(parametersColumnAdvanced, inputsColumnAdvanced, ParamEmptyAdvanced);
  }
}

// Function to show all sections
function showAllSections(parametersColumn, inputsColumn, paramEmpty) {

  Array.from(parametersColumn).forEach((element) => {
    element.style.display = "block";
  });
  Array.from(inputsColumn).forEach((element) => {
    element.style.display = "block";
  });
  paramEmpty.style.display = "none";
}

// Hide DDA Section
function hideDDASection(parametersColumn,inputsColumn,paramEmpty) {
    key = ["DDA data analysis","DIA data analysis"]
    occurrence = 0
    const parameterElements = Array.from(parametersColumn);
    const inputElements = (inputsColumn);
    const targetIndex = parameterElements.findIndex(
      (element) => element.textContent === key[0]
    );
    
    if (targetIndex !== -1) {
      console.log("index is -1 or not found?")
      parameterElements[targetIndex].style.display = "none";
      inputElements[targetIndex].style.display = "none";

      let count = 0;
      for (let i = targetIndex + 1; i < parameterElements.length; i++) {
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

// Hide DIA Section
function hideDIASection(parametersColumn,inputsColumn,paramEmpty) {
  key = ["DIA data analysis","lipid annotation"]
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

// Hide Annotate Section
function hideAnnotateSection(parametersColumn,inputsColumn,paramEmpty) {
  key = ["lipid annotation","miscellaneous"]
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

// Update which file upload options are available depending on checkboxes
function UpdateFileOptions() {
  const ddaFileRegion = document.getElementById("dda-file-region");
  const diaFileRegion = document.getElementById("dia-file-region");
  const annFileSection = document.getElementById('annotate-file-region');
  ddaFileRegion.style.display = (checkboxes.general.dda.checked || checkboxes.advanced.dda.checked) ? "block" : "none";
  diaFileRegion.style.display = (checkboxes.general.dia.checked || checkboxes.advanced.dia.checked) ? "block" : "none";
  annFileSection.style.display = (checkboxes.general.annotate.checked || checkboxes.advanced.annotate.checked) ? "block" : "none";
}


// Python Results Box scroll to bottom by default
function scrollToBottom(element) {
  element.scrollTo({
    top: element.scrollHeight,
    behavior: 'smooth',
    block: 'end',
  });
}

// Radio Box checker for database options
function getSelectedDatabaseOption() {
  let radios = document.querySelectorAll('.section-container input[name="db_option"]');
  
  for (let radio of radios) {
      if (radio.checked) {
          return radio.value;
      }
  }
}

// Save directorypath for experiment results
function selectSaveDirectory() {
  window.api.send('open-directory-dialog');
}

window.api.receive('directory-selected', (path) => {
  console.log("Selected directory:", path);
  document.getElementById('selected-directory').value = path;
});

// Database New Name for Experiment
function UpdateExpName() {
  const TFnew = document.getElementById("create-new-option").checked
  const TFsave = document.getElementById("save-params").checked
  if (TFnew === true || TFsave === true) {
    document.getElementById("new-db-name-container").style.display = "flex"
    document.getElementById("selected-directory-container").style.display = "flex"
  }
  else {
    document.getElementById("new-db-name-container").style.display = "none"
    document.getElementById("selected-directory-container").style.display = "none"
  }
}

// Annotation Options for experiment
function UpdateAnnotateOptions() {
  const TF = checkboxes.general.annotate.checked
  console.log("TF: ", TF)

  if (TF === true) {
    document.getElementById("annotate-options").style.display = "flex"
    document.getElementById("annotate-behavior").style.display = "flex"
  }
  else {
    document.getElementById("annotate-options").style.display = "none"
    document.getElementById("annotate-behavior").style.display = "none"
  }
}

function UpdateDatabaseOptions() {
  const dda = checkboxes.general.dda.checked
  const dia = checkboxes.general.dia.checked

  if (dda === true || dia === true) {
    document.getElementById("db-options").style.display = "flex"
  }
  else {
    document.getElementById("db-options").style.display = "none"
  }
}


// Receive Python Experiment Results to display
window.api.receive('python-result-experiment', (result) => {
  console.log('Received result:', result);
  outputBox.innerText += result; // Append the result to the output box
  scrollToBottom(outputBox);
});


// Get List of files from Array
function fileListToArray(fileList) {
  return Array.from(fileList.getElementsByTagName('li')).map((listItem) => {
    const fileText = listItem.querySelector('.file-text');
    console.log("fileText:",fileText);
    // Return only the path for each file
    return fileText.dataset.path;
  });
}

// Run Experiment in Python. Format all inputs to match experiment requirements
function RunExperiment() {
  const selectedDatabaseOption = getSelectedDatabaseOption()
  const selectedDatabaseName = document.getElementById("experiment-name").value
  const selectedSaveLocation = document.getElementById("selected-directory").value
  const isIonizationPositive = document.getElementById("ionization-positive").checked;
  const isAnnotationAppend = document.getElementById("annotation-append").checked;
  const filesDDA = fileListToArray(fileListDDA);
  const filesDIA = fileListToArray(fileListDIA);
  const filesDatabase = fileListToArray(fileListDatabase);
  const filesAnnotation = fileListToArray(fileListAnnotation);
  let currentHeader = null;
  let currentSubheader = null;
  const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');
  const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
  const isBehaviorDefault = document.getElementById("behavior-custom").checked;
  const TFsave = document.getElementById("save-params").checked
  const TFnew = document.getElementById("create-new-option").checked
  const TFoverwrite = document.getElementById("overwrite-option").checked
  const TFappend = document.getElementById("append-option").checked

  // Check if run options that the user selected make sense
  if ((TFsave === true || TFnew === true) && (selectedDatabaseName === '' || selectedSaveLocation === '')) {
    alert("Please enter an experiment name and save location. ");
    return;  // Return early to stop further execution
  }

  if (checkboxes.advanced.dda.checked && filesDDA.length === 0) {
      alert("DDA processing is selected but no DDA files are provided. ");
      return;
  }

  if (checkboxes.advanced.dia.checked && filesDIA.length === 0) {
      alert("DIA processing is selected but no DIA files are provided. ");
      return;
  }

  if ((TFappend || TFoverwrite) && filesDatabase.length === 0) {
      alert("Append/Overwrite Database option is selected but no Database files are provided. ");
      return;
  }

  if (!checkboxes.advanced.dda.checked && !checkboxes.advanced.dia.checked && !checkboxes.advanced.annotate.checked) {
      alert("None of the DDA processing, DIA processing, or Annotation options are selected. ");
      return;
  }



  // If save parameters is selected, save them.
  if (TFsave === true ) {
    if (selectedDatabaseName !== '' && selectedSaveLocation !== '') {
    WriteToYaml('duo-inputs-column-both-advanced',selectedDatabaseName, selectedSaveLocation)
    }
    else {
      WriteToYaml('duo-inputs-column-both-advanced')
    }
  }


  const parameters = {
      dda: {},
      dia: {},
      annotation: {},
      misc: {
        dia_store_blobs: true,
        do_dda_processing: false,
        do_dia_processing: false,
        do_annotation: false,
        overwrite_annotations: false,
        ionization: "POS"
      }
    };
  
  const inputOutput = {
    dda_data_files: [],
    dia_data_files: [],
    results_db: [],
    lipid_class_scdb_config: []
  };

  const gui_params = {
    db_pick: selectedDatabaseOption,
    db_name: selectedDatabaseName,
    save_loc: selectedSaveLocation
  }

  if (checkboxes.advanced.dda.checked === true) {
    parameters.misc.do_dda_processing = true;
  }
  
  if (checkboxes.advanced.dia.checked === true) {
    parameters.misc.do_dia_processing = true;
  }

  if (checkboxes.advanced.annotate.checked === true) {
    parameters.misc.do_annotation = true;
  }

  if (isAnnotationAppend === false) {
    parameters.misc.overwrite_annotations = true;
  }

  if (isIonizationPositive === false) {
    parameters.misc.ionization = "NEG";
  }

  // Add in parameter values
  for (let i = 0; i < inputs.length; i++) {
    const input = inputs[i];
    const input2 = inputs2[i];

    if (input2.id === "dda" || input2.id === "dia" || input2.id === "annotation") {
        currentHeader = input2.id;
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

  // Update files with those selected by user
  inputOutput['dda_data_files'] = filesDDA;
  inputOutput['dia_data_files'] = filesDIA;
  inputOutput['results_db'] = filesDatabase[0];  // Only one file allowed

  // Annotation File is only assigned if annotation behaivor is set to custom file.
  if (isBehaviorDefault === true) {
    inputOutput['lipid_class_scdb_config'] = filesAnnotation[0]; // Only one file allowed
  }

  console.log(gui_params)
  const options = {
    pythonPath: 'python3',
    args: {
      input_output: inputOutput,
      params: parameters,
      options: gui_params
    }
  };

  outputBox.innerText += "Experiment Starting. Please give it one minute to begin. " + '\n';
  window.api.send('run-python-experiment', options);
  disableButton()
} 


// This should prevent users from clicking run experiment twice in a row.
function disableButton() {
  const button = document.getElementById('run-btn');
  button.disabled = true;
  // Set a timeout for 5 seconds (5000 milliseconds) to re-enable the button
  setTimeout(() => {
      button.disabled = false;
  }, 5000);
}