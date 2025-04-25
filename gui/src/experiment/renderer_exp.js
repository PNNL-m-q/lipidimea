
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

// Handler for Calibrate button
function calibrateDIA() {
  const dbFile = `${document.getElementById('selected-directory').value}/${document.getElementById('experiment-name').value}.db`;
  window.api.send('run-lipidimea-cli-steps', {
    steps: [
      { cmd: ["dia", "calibrate_ccs", dbFile, "-0.082280", "0.132301", "9"], desc: "Calibrating CCS" }
    ]
  });
}

// New optional config file pickers
const selectButtonFragRulesConfig   = document.getElementById('select-button-frag-rules-config');
const fileInputFragRulesConfig      = document.getElementById('frag-rules-config-file-input');
const fileListFragRulesConfig       = document.getElementById('file-list-frag-rules-config');
const selectButtonCcsTrendsConfig   = document.getElementById('select-button-ccs-trends-config');
const fileInputCcsTrendsConfig      = document.getElementById('ccs-trends-config-file-input');
const fileListCcsTrendsConfig       = document.getElementById('file-list-ccs-trends-config');
const selectButtonRtRangeConfig     = document.getElementById('select-button-rt-range-config');
const fileInputRtRangeConfig        = document.getElementById('rt-range-config-file-input');
const fileListRtRangeConfig         = document.getElementById('file-list-rt-range-config');
const selectButtonSumCompConfig     = document.getElementById('select-button-sum-comp-config');
const fileInputSumCompConfig        = document.getElementById('sum-comp-config-file-input');
const fileListSumCompConfig         = document.getElementById('file-list-sum-comp-config');

// Arrays to hold the selected files
const filesFragRulesConfig   = [];
const filesCcsTrendsConfig   = [];
const filesRtRangeConfig     = [];
const filesSumCompConfig     = [];

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


// Whenever the DIA checkbox changes, enable/disable the Calibrate button
// [checkboxes.general.dia, checkboxes.advanced.dia].forEach(cb => {
//   cb.addEventListener('change', () => {
//     const diaOn = checkboxes.general.dia.checked || checkboxes.advanced.dia.checked;
//     calibrateBtn.disabled = !diaOn;
//   });
// });


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
      const cb = checkboxes[type][mode];
      cb.addEventListener("change", handleCheckboxChange);
      cb.addEventListener("change", UpdateFileOptions);
      // cb.addEventListener("change", UpdateCalibrateOptions);
  }
}
document.addEventListener('DOMContentLoaded', () => {
  window.api.send('getDefaults');
  UpdateCalibrateOptions();
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
  
// if (selectButtonAnnotation) {
//   selectButtonAnnotation.addEventListener('click', () => {
//     fileInputAnnotation.click();
//   }
// )};

// if (selectButtonDatabase) {
//   selectButtonDatabase.addEventListener('click', () => {
//     fileInputDatabase.click();
//   }
// )};

if (selectButtonFragRulesConfig) {
  selectButtonFragRulesConfig.addEventListener('click', () => {
    fileInputFragRulesConfig.click();
  });
}
if (selectButtonCcsTrendsConfig) {
  selectButtonCcsTrendsConfig.addEventListener('click', () => {
    fileInputCcsTrendsConfig.click();
  });
}
if (selectButtonRtRangeConfig) {
  selectButtonRtRangeConfig.addEventListener('click', () => {
    fileInputRtRangeConfig.click();
  });
}
if (selectButtonSumCompConfig) {
  selectButtonSumCompConfig.addEventListener('click', () => {
    fileInputSumCompConfig.click();
  });
}


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

if (fileInputFragRulesConfig) {
  fileInputFragRulesConfig.addEventListener('change', () => {
    handleFileSelection(fileInputFragRulesConfig, fileListFragRulesConfig, filesFragRulesConfig);
  });
}
if (fileInputCcsTrendsConfig) {
  fileInputCcsTrendsConfig.addEventListener('change', () => {
    handleFileSelection(fileInputCcsTrendsConfig, fileListCcsTrendsConfig, filesCcsTrendsConfig);
  });
}
if (fileInputRtRangeConfig) {
  fileInputRtRangeConfig.addEventListener('change', () => {
    handleFileSelection(fileInputRtRangeConfig, fileListRtRangeConfig, filesRtRangeConfig);
  });
}
if (fileInputSumCompConfig) {
  fileInputSumCompConfig.addEventListener('change', () => {
    handleFileSelection(fileInputSumCompConfig, fileListSumCompConfig, filesSumCompConfig);
  });
}


// if (fileInputDatabase) {
//   fileInputDatabase.addEventListener('change', () => {
//     handleFileSelection(fileInputDatabase, fileListDatabase, filesDatabase);
//   });
// }

// if (fileInputAnnotation) {
//   fileInputAnnotation.addEventListener('change', () => {
//     handleFileSelection(fileInputAnnotation, fileListAnnotation, filesAnnotation);
//   });
// }

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
// window.api.receive('returnDefaults', (data) => {
//     data = { PARAMETERS: data };

//     if (loadyamlonce === true) {
//         loadyamlonce = false;

//         if (data) {
//             const parametersBoth = { ...data.PARAMETERS.dda, ...data.PARAMETERS.dia, ...data.PARAMETERS.annotation };
//             const mainElementTop = Object.keys(data.PARAMETERS);
//             const sectionsTopBoth = mainElementTop.filter(display_name => display_name !== 'misc');

//             const duoinputsColumnBothGeneral = document.getElementById('duo-inputs-column-both-general');
//             const duoinputsColumnBothAdvanced = document.getElementById('duo-inputs-column-both-advanced');

//             sectionsTopBoth.forEach((sectionTopBoth) => {

//                 // TODO: Text formatting, some of the keys/values from the YAML are ugly
//                 const sectionsBoth = Object.keys(data.PARAMETERS[sectionTopBoth]).filter(key => key !== "misc" && key !== "display_name");

//                 createHeaderElement(data.PARAMETERS[sectionTopBoth].display_name, duoinputsColumnBothAdvanced, sectionTopBoth);
//                 createHeaderElement(data.PARAMETERS[sectionTopBoth].display_name, duoinputsColumnBothGeneral, sectionTopBoth);

//                 sectionsBoth.forEach((sectionBoth) => {
//                     const sectionDataBoth = parametersBoth[sectionBoth];
//                     const generalValues = Object.entries(sectionDataBoth).filter(([key, value]) => !value.advanced && key !== "display_name");
//                     const allValues = Object.entries(sectionDataBoth).filter(([key]) => key !== "display_name");

//                     if (generalValues.length > 0) {
//                         createSubHeaderElement(sectionDataBoth.display_name, duoinputsColumnBothGeneral,sectionBoth);

//                         generalValues.forEach(([key, value]) => {
//                             createParameterElement(value.display_name, key, value.description, duoinputsColumnBothGeneral);
//                             createInput(value.type, value.default, key, duoinputsColumnBothGeneral, duoinputsColumnBothAdvanced);
//                         });
//                     }

//                     if (allValues.length > 0) {
//                         createSubHeaderElement(sectionDataBoth.display_name, duoinputsColumnBothAdvanced,sectionBoth);

//                         allValues.forEach(([key, value]) => {
//                             createParameterElement(value.display_name, key, value.description, duoinputsColumnBothAdvanced);
//                             createInput(value.type, value.default, key, duoinputsColumnBothAdvanced, duoinputsColumnBothGeneral);
//                         });
//                     }
//                 });
//             });
//         }
//     }
// });

window.api.receive('returnDefaults', (data) => {
  data = { PARAMETERS: data };
  if (!loadyamlonce) return;
  loadyamlonce = false;
  if (!data) return;

  const defaultParams = data.PARAMETERS;
  const sectionsTop = Object.keys(defaultParams).filter(k => k !== 'misc');

  const generalContainer = document.getElementById('duo-inputs-column-both-general');
  const advContainer     = document.getElementById('duo-inputs-column-both-advanced');

  sectionsTop.forEach((sectionKey) => {
    const sectionMeta = defaultParams[sectionKey];
    const headerText  = sectionMeta.display_name;

    // Section headers in both tabs
    createHeaderElement(headerText, generalContainer, sectionKey);
    createHeaderElement(headerText, advContainer, sectionKey);

    // Iterate through each subsection under this section
    Object.keys(sectionMeta)
      .filter(subKey => subKey !== 'display_name')
      .forEach((subKey) => {
        const node = sectionMeta[subKey];

        // --- Leaf param? (has a default) ---
        if (node && typeof node === 'object' && node.hasOwnProperty('default')) {
          // General tab: only non-advanced
          if (!node.advanced) {
            createParameterElement(
              node.display_name, subKey, node.description, generalContainer
            );
            createInput(node, subKey, generalContainer, advContainer);
          }
          // Advanced tab: all parameters
          createParameterElement(
            node.display_name, subKey, node.description, advContainer
          );
          createInput(node, subKey, advContainer, generalContainer);

        // --- Grouped params (no direct default) ---
        } else if (node && typeof node === 'object') {
          // Subheaders in both tabs
          createSubHeaderElement(
            node.display_name, generalContainer, subKey
          );
          createSubHeaderElement(
            node.display_name, advContainer, subKey
          );

          // Split children by advanced flag
          const entries = Object.entries(node)
                                 .filter(([k]) => k !== 'display_name');
          const generalEntries = entries.filter(([,meta]) => !meta.advanced);
          const advEntries     = entries.filter(([,meta]) =>  meta.advanced);

          // Render non-advanced in General
          generalEntries.forEach(([paramKey, paramMeta]) => {
            createParameterElement(
              paramMeta.display_name, paramKey, paramMeta.description, generalContainer
            );
            createInput(paramMeta, paramKey, generalContainer, advContainer);
          });

          // Render **all** in Advanced (first non-advanced, then advanced)
          [...generalEntries, ...advEntries].forEach(([paramKey, paramMeta]) => {
            createParameterElement(
              paramMeta.display_name, paramKey, paramMeta.description, advContainer
            );
            createInput(paramMeta, paramKey, advContainer, generalContainer);
          });
        }
      });
  });
});







// A series of functions to create the param elements
// Ideally style should be formatted in css.
// Note to self - fix this if time.
function createHeaderElement(textContent, parentNode, ID) {
  const element = document.createElement('p');
  element.textContent = textContent;
  element.style.textAlign = 'left';
  element.style.fontSize = '24px';
  element.style.fontWeight = 'bold';
  element.style.gridColumn = 'span 2';
  element.id = ID;
  element.key = 'Ignore';
  parentNode.appendChild(element);

  createHiddenInput(parentNode);
}

function createSubHeaderElement(textContent, parentNode, ID) {
  const element = document.createElement('p');
  element.textContent = textContent;
  element.id = ID;
  element.style.textAlign = 'left';
  element.style.fontSize = '20px';
  element.style.fontWeight = 'bold';
  element.style.gridColumn = 'span 2';
  element.key = 'Ignore';
  parentNode.appendChild(element);

  createHiddenInput(parentNode);
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

// function createInput(type, value, id, parentNode, otherTab) {
//     const inputElement = document.createElement('input');
//     inputElement.type = type;
//     inputElement.value = value;
//     inputElement.id = id;
//     inputElement.style.gridColumn = '2';
//     inputElement.key = 'Ignore'; // Assign 'Ignore' to key property

//     inputElement.addEventListener('change', (event) => {
//         const updatedValue = event.target.value;
//         const oldInputs = Array.from(otherTab.getElementsByTagName('input'));
//         const index = oldInputs.findIndex((input) => input.id === event.target.id);

//         if (index !== -1) {
//             oldInputs[index].value = updatedValue;
//         }
//     });

//     parentNode.appendChild(inputElement);
// }

/**
 * Creates the right kind of input(s) for a parameter, based on its metadata.
 *
 * @param {object} paramMeta  The metadata object with .type and .default
 * @param {string} id         The base id for the input element(s)
 * @param {HTMLElement} parentNode  Where to append the input(s)
 * @param {HTMLElement} otherTab    The parallel tab container to sync values
 */
function createInput(paramMeta, id, parentNode, otherTab) {
  let element;

  if (id === 'ionization') {
    const msg = document.createElement('span');
    msg.textContent = 'Select in "Run Experiment" Tab.';
    msg.style.gridColumn = '2';
    msg.style.fontStyle = 'italic';
    parentNode.appendChild(msg);
    return;
  }

  if (paramMeta.display_name.toLowerCase().includes(' file')) {
    const msg = document.createElement('span');
    msg.textContent = 'Select file in "File Upload" Tab.';
    msg.style.gridColumn = '2';
    msg.style.fontStyle = 'italic';
    parentNode.appendChild(msg);
    return;
  }
  

  switch (paramMeta.type) {
    case 'bool':
      // checkbox for booleans
      element = document.createElement('input');
      element.type = 'checkbox';
      element.checked = Boolean(paramMeta.default);
      element.style.justifySelf = 'left';
      break;

      case 'range':
        // wrapper for both min/max groups
        element = document.createElement('div');
        element.style.display       = 'flex';
        element.style.width         = '100%';
        element.dataset.origDisplay = 'flex';
        element.style.gridColumn    = '2';
        element.style.gap           = '1rem';
        element.style.alignItems    = 'center';

        // Common input style
        const inputHeight = '2rem';     // adjust to match your other inputs
        const inputPadding = '0.25rem'; // same as your CSS for other inputs

        // ── Minimum group ──
        const minWrapper = document.createElement('div');
        minWrapper.style.display    = 'flex';
        minWrapper.style.flex       = '1';
        minWrapper.style.alignItems = 'center';
        minWrapper.style.gap        = '0.25rem';
        const minLabel = document.createElement('label');
        minLabel.textContent = 'Minimum:';
        minLabel.htmlFor     = `${id}_min`;
        const minIn = document.createElement('input');
        minIn.type    = 'number';
        minIn.id      = `${id}_min`;
        minIn.value   = paramMeta.default.min;
        minIn.style.width   = '100%';
        minIn.style.height  = inputHeight;
        minIn.style.padding = inputPadding;
        minWrapper.append(minLabel, minIn);

        // ── Maximum group ──
        const maxWrapper = document.createElement('div');
        maxWrapper.style.display    = 'flex';
        maxWrapper.style.flex       = '1';
        maxWrapper.style.alignItems = 'center';
        maxWrapper.style.gap        = '0.25rem';
        const maxLabel = document.createElement('label');
        maxLabel.textContent = 'Maximum:';
        maxLabel.htmlFor     = `${id}_max`;
        const maxIn = document.createElement('input');
        maxIn.type    = 'number';
        maxIn.id      = `${id}_max`;
        maxIn.value   = paramMeta.default.max;
        maxIn.style.width   = '100%';
        maxIn.style.height  = inputHeight;
        maxIn.style.padding = inputPadding;
        maxWrapper.append(maxLabel, maxIn);

        // assemble
        element.append(minWrapper, maxWrapper);

        // sync behavior
        [minIn, maxIn].forEach(inp => {
          inp.addEventListener('change', e => {
            const mirror = otherTab.querySelector(`#${e.target.id}`);
            if (mirror) mirror.value = e.target.value;
          });
        });
        break;

    case 'int':
    case 'float':
      // numeric input
      element = document.createElement('input');
      element.type = 'number';
      element.step = paramMeta.type === 'int' ? '1' : 'any';
      element.value = paramMeta.default ?? '';
      break;

    default:
      // text fallback
      element = document.createElement('input');
      element.type = 'text';
      element.value = paramMeta.default ?? '';
  }

  // Common setup (for single-element cases, or wrap container)
  if (paramMeta.type !== 'range') {
    element.id = id;
    element.style.gridColumn = '2';
    element.key = 'Ignore';
    // Sync across tabs
    element.addEventListener('change', e => {
      const mirror = otherTab.querySelector(`#${id}`);
      if (mirror) {
        if (paramMeta.type === 'bool') {
          mirror.checked = e.target.checked;
        } else {
          mirror.value = e.target.value;
        }
      }
    });
  } else {
    // the wrapper div gets the grid styling
    element.style.gridColumn = '2';
  }

  parentNode.appendChild(element);
}



// Write User Updated Parameter Values to file
// function WriteToYaml(i,name,location) {
//   const inputValues = {};
//   const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
//   const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');

//   let currentHeader = null;
//   let currentSubheader = null;
//   for (let i = 0; i < inputs.length; i++) {
//     const input = inputs[i];
//     let input2 = inputs2[i];

//     // Detect if the element represents a header
//     if (input2.id === "dda" || input2.id === "dia" || input2.id === "annotation") {
//       currentHeader = input2.id;
//       inputValues[currentHeader] = {};
//       currentSubheader = null;  // Reset subheader when a new header is detected
//       continue;
//     }
//     // Detect if the element represents a subheader
//     if (input2 && input2.key === "Ignore") {
//       currentSubheader = input2.id;
//       inputValues[currentHeader][currentSubheader] = {};  // Initialize a sub dictionary for the subheader
//       continue;
//     }
//     // If we're within a header and subheader, nest the input values accordingly
//     if (input && input2 && input.style.display != "none") {
//       if (currentHeader && currentSubheader) {
//         inputValues[currentHeader][currentSubheader][input2.id] = input.value;
//       } else if (currentHeader) {
//         inputValues[currentHeader][input2.id] = input.value;
//       } else {
//         inputValues[input2.id] = input.value;
//       }
//     }
//   }

//   if (location === undefined || name === undefined){
//   const options = {
//     pythonPath: 'python3',
//     args: inputValues,
//   };
//   window.api.send('request-filename-and-directory');

//   window.api.receive('selected-param-save-directory', (savePath) => {
//     const options = {
//         pythonPath: 'python3',
//         args: inputValues,
//         path: savePath
//     };
//     window.api.send('run-python-yamlwriter', options);
//   });
// }
// else {
//   const options = {
//     pythonPath: 'python3',
//     args: inputValues,
//     name: name,
//     location: location
// };
//   window.api.send('run-python-yamlwriter', options);

// }

// }
/**
 * Read every <p> + <input> pair in `containerId` and
 * return an object like { dda: {...}, dia: {...}, annotation: {...}, misc: {...} }
 */
/**
 * Walk through <p id="..."> labels in the given container,
 * match them to their inputs (or paired min/max), and
 * assemble a nested { dda:{}, dia:{}, annotation:{} } object
 * with proper types.
 */


// Works for DDA but not DIA
function collectAdvancedParams(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return {};

  const sections = {};
  let currentHeader = null;
  let currentSub    = null;

  // Only look at <p> elements that have an id
  const labels = Array.from(container.querySelectorAll('p[id]'));
  labels.forEach(label => {
    const key = label.id;

    // Top‐level section headers
    if (['dda','dia','annotation','misc'].includes(key)) {
      currentHeader = key;
      sections[currentHeader] = {};
      currentSub = null;
      return;
    }

    // Sub‐section headers (you set label.key = 'Ignore')
    if (label.key === 'Ignore') {
      currentSub = key;
      sections[currentHeader][currentSub] = {};
      return;
    }

    // Find the next sibling INPUT or DIV (range wrapper)
    let sib = label.nextElementSibling;
    while (sib && !(sib.tagName === 'INPUT' || sib.tagName === 'DIV')) {
      sib = sib.nextElementSibling;
    }
    if (!sib) return;

    // Determine value
    let value;
    if (sib.tagName === 'DIV') {
      // Range: expect two number inputs inside the DIV
      const inputs = sib.getElementsByTagName('input');
      const parse = v => {
        const t = v.trim();
        return t === '' ? null : parseFloat(t);
      };
      value = {
        min: parse(inputs[0].value),
        max: parse(inputs[1].value)
      };
    } else {
      // Single <input>
      if (sib.type === 'checkbox') {
        value = sib.checked;
      } else {
        const t = sib.value.trim();
        if (t === '') value = null;
        else if (!isNaN(t)) value = parseFloat(t);
        else value = t;
      }
    }

    // Assign into the nested object
    if (!currentHeader) return;
    if (currentSub) {
      sections[currentHeader][currentSub][key] = value;
    } else {
      sections[currentHeader][key] = value;
    }
  });

  return sections;
}

/**
 * Write only one category out to YAML
 */
function WriteCategoryYaml(containerId, categoryKey, name, saveLoc) {
  const allSections = collectAdvancedParams(containerId);
  const section     = allSections[categoryKey] || {};

  if (categoryKey === "annotation") {
    // 1) Ionization
    const ionPos = document.getElementById("ionization-positive").checked;
    section.ionization = ionPos ? "POS" : "NEG";

    // 2) Optional file‐inputs
    const injectFile = (ulId, pathSetter) => {
      const ul = document.getElementById(ulId);
      if (!ul) return;
      const files = fileListToArray(ul);
      if (files.length) pathSetter(files[0]);
    };

    // Fragmentation rules config → frag_rules.config
    injectFile("file-list-frag-rules-config", 
      fp => section.frag_rules = { ...(section.frag_rules||{}), config: fp });

    // CCS trends config → ccs_trends.config
    injectFile("file-list-ccs-trends-config", 
      fp => section.ccs_trends = { ...(section.ccs_trends||{}), config: fp });

    // RT range config → rt_range_config
    injectFile("file-list-rt-range-config",
      fp => section.rt_range_config = fp);

    // Sum composition config → sum_comp.config
    injectFile("file-list-sum-comp-config",
      fp => section.sum_comp = { ...(section.sum_comp||{}), config: fp });
  }

  if (!Object.keys(section).length) {
    outputBox.innerText += `\n(No parameters for ${categoryKey}, skipping)\n`;
    return;
  }

  const options = {
    pythonPath: "python3",
    args:       section,
    name:       name,
    location:   saveLoc
  };
  window.api.send("run-python-yamlwriter", options);
  outputBox.innerText += `Wrote ${categoryKey.toUpperCase()} config to ${saveLoc}/${name}.yaml\n`;
}




function WriteToYaml(containerId, name, location) {
  const inputValues = {};
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`WriteToYaml: container "${containerId}" not found`);
    return;
  }

  // Grab the <p> labels and <input> elements under this container
  const pEls  = Array.from(container.getElementsByTagName('p'));
  const inEls = Array.from(container.getElementsByTagName('input'));

  // Only iterate over the range where both exist
  const count = Math.min(pEls.length, inEls.length);

  let currentHeader   = null;
  let currentSubheader = null;
  for (let i = 0; i < count; i++) {
    const label = pEls[i];
    const inp   = inEls[i];

    // Skip any of the hidden header placeholders
    if (!label.id) continue;

    // Detect section headers (these were your DDA/DIA/annotation top‑level IDs)
    if (['dda','dia','annotation'].includes(label.id)) {
      currentHeader = label.id;
      inputValues[currentHeader] = {};
      currentSubheader = null;
      continue;
    }

    // Detect sub‑section headers
    if (label.key === 'Ignore') {
      currentSubheader = label.id;
      inputValues[currentHeader][currentSubheader] = {};
      continue;
    }

    // Otherwise, it’s a real parameter
    const key = label.id;
    let val;
    if (inp.type === 'checkbox') {
      val = inp.checked;
    } else {
      val = inp.value;
    }

    // Nest under header/subheader
    if (currentHeader && currentSubheader) {
      inputValues[currentHeader][currentSubheader][key] = val;
    } else if (currentHeader) {
      inputValues[currentHeader][key] = val;
    } else {
      inputValues[key] = val;
    }
  }

  // Now fire off the IPC to write the YAML
  const options = { pythonPath: 'python3', args: inputValues };
  if (name && location) {
    options.name     = name;
    options.location = location;
  }

  window.api.send('run-python-yamlwriter', options);
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
  const isDDA      = checkboxes.general.dda.checked || checkboxes.advanced.dda.checked;
  const isDIA      = checkboxes.general.dia.checked || checkboxes.advanced.dia.checked;
  const isAnnotate = checkboxes.general.annotate.checked || checkboxes.advanced.annotate.checked;

  // First, show everything again
  showAllSections(
    document.getElementById('duo-inputs-column-both-general'),
    ParamEmptyGeneral
  );
  showAllSections(
    document.getElementById('duo-inputs-column-both-advanced'),
    ParamEmptyAdvanced
  );

  // Now hide each section if its box is unchecked
  if (!isDDA) {
    // hide from <p id="dda"> up to (but not including) <p id="dia">
    hideSection('dda', 'dia', document.getElementById('duo-inputs-column-both-general'), ParamEmptyGeneral);
    hideSection('dda', 'dia', document.getElementById('duo-inputs-column-both-advanced'), ParamEmptyAdvanced);
  }
  if (!isDIA) {
    // hide from <p id="dia"> up to <p id="annotation">
    hideSection('dia', 'annotation', document.getElementById('duo-inputs-column-both-general'), ParamEmptyGeneral);
    hideSection('dia', 'annotation', document.getElementById('duo-inputs-column-both-advanced'), ParamEmptyAdvanced);
  }
  if (!isAnnotate) {
    // hide from <p id="annotation"> through end
    hideSection('annotation', null, document.getElementById('duo-inputs-column-both-general'), ParamEmptyGeneral);
    hideSection('annotation', null, document.getElementById('duo-inputs-column-both-advanced'), ParamEmptyAdvanced);
  }

  // If all three are off, show the empty notices
  if (!isDDA && !isDIA && !isAnnotate) {
    ParamEmptyGeneral.style.display = 'flex';
    ParamEmptyAdvanced.style.display = 'flex';
  }

  UpdateCalibrateOptions();

}


function showAllSections(container, emptyNotice) {
  Array.from(container.children).forEach((child) => {
    if (child.dataset.origDisplay) {
      child.style.display = child.dataset.origDisplay;
    } else {
      child.style.display = '';
    }
  });
  emptyNotice.style.display = 'none';
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
// function UpdateFileOptions() {
//   const ddaFileRegion = document.getElementById("dda-file-region");
//   const diaFileRegion = document.getElementById("dia-file-region");
//   const annFileSection = document.getElementById('annotate-file-region');
//   ddaFileRegion.style.display = (checkboxes.general.dda.checked || checkboxes.advanced.dda.checked) ? "block" : "none";
//   diaFileRegion.style.display = (checkboxes.general.dia.checked || checkboxes.advanced.dia.checked) ? "block" : "none";
//   annFileSection.style.display = (checkboxes.general.annotate.checked || checkboxes.advanced.annotate.checked) ? "block" : "none";
// }

function UpdateFileOptions() {
  const isDDA      = checkboxes.general.dda.checked || checkboxes.advanced.dda.checked;
  const isDIA      = checkboxes.general.dia.checked || checkboxes.advanced.dia.checked;
  const isAnnotate = checkboxes.general.annotate.checked || checkboxes.advanced.annotate.checked;

  // Existing regions
  const ddaFileRegion       = document.getElementById("dda-file-region");
  const diaFileRegion       = document.getElementById("dia-file-region");
  // const annFileRegion       = document.getElementById("annotate-file-region");

  // New annotation‑config file regions
  const fragRulesRegion     = document.getElementById("frag-rules-config-file-region");
  const ccsTrendsRegion     = document.getElementById("ccs-trends-config-file-region");
  const rtRangeRegion       = document.getElementById("rt-range-config-file-region");
  const sumCompRegion       = document.getElementById("sum-comp-config-file-region");

  // Show/hide based on DDA/DIA/Annotate
  ddaFileRegion.style.display   = isDDA      ? "block" : "none";
  diaFileRegion.style.display   = isDIA      ? "block" : "none";
  // annFileRegion.style.display   = isAnnotate ? "block" : "none";

  // Only show these four when annotation is on
  fragRulesRegion.style.display = isAnnotate ? "block" : "none";
  ccsTrendsRegion.style.display = isAnnotate ? "block" : "none";
  rtRangeRegion.style.display   = isAnnotate ? "block" : "none";
  sumCompRegion.style.display   = isAnnotate ? "block" : "none";
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
// function fileListToArray(fileList) {
//   return Array.from(fileList.getElementsByTagName('li')).map((listItem) => {
//     const fileText = listItem.querySelector('.file-text');
//     console.log("fileText:",fileText);
//     // Return only the path for each file
//     return fileText.dataset.path;
//   });
// }

function fileListToArray(fileList) {
  if (!fileList) return [];
  return Array.from(fileList.getElementsByTagName('li'))
    .map(listItem => {
      const ft = listItem.querySelector('.file-text');
      return ft && ft.dataset && ft.dataset.path;
    })
    .filter(path => Boolean(path));
}

// // Run Experiment in Python. Format all inputs to match experiment requirements
// function RunExperiment() {
//   const selectedDatabaseOption = getSelectedDatabaseOption()
//   const selectedDatabaseName = document.getElementById("experiment-name").value
//   const selectedSaveLocation = document.getElementById("selected-directory").value
//   const isIonizationPositive = document.getElementById("ionization-positive").checked;
//   const isAnnotationAppend = document.getElementById("annotation-append").checked;
//   const filesDDA = fileListToArray(fileListDDA);
//   const filesDIA = fileListToArray(fileListDIA);
//   const filesDatabase = fileListToArray(fileListDatabase);
//   const filesAnnotation = fileListToArray(fileListAnnotation);
//   let currentHeader = null;
//   let currentSubheader = null;
//   const inputs = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('input');
//   const inputs2 = document.getElementById("duo-inputs-column-both-advanced").getElementsByTagName('p');
//   const isBehaviorDefault = document.getElementById("behavior-custom").checked;
//   const TFsave = document.getElementById("save-params").checked
//   const TFnew = document.getElementById("create-new-option").checked
//   const TFoverwrite = document.getElementById("overwrite-option").checked
//   const TFappend = document.getElementById("append-option").checked

//   // Check if run options that the user selected make sense
//   if ((TFsave === true || TFnew === true) && (selectedDatabaseName === '' || selectedSaveLocation === '')) {
//     alert("Please enter an experiment name and save location. ");
//     return;  // Return early to stop further execution
//   }

//   if (checkboxes.advanced.dda.checked && filesDDA.length === 0) {
//       alert("DDA processing is selected but no DDA files are provided. ");
//       return;
//   }

//   if (checkboxes.advanced.dia.checked && filesDIA.length === 0) {
//       alert("DIA processing is selected but no DIA files are provided. ");
//       return;
//   }

//   if ((TFappend || TFoverwrite) && filesDatabase.length === 0) {
//       alert("Append/Overwrite Database option is selected but no Database files are provided. ");
//       return;
//   }

//   if (!checkboxes.advanced.dda.checked && !checkboxes.advanced.dia.checked && !checkboxes.advanced.annotate.checked) {
//       alert("None of the DDA processing, DIA processing, or Annotation options are selected. ");
//       return;
//   }



//   // If save parameters is selected, save them.
//   if (TFsave === true ) {
//     if (selectedDatabaseName !== '' && selectedSaveLocation !== '') {
//     WriteToYaml('duo-inputs-column-both-advanced',selectedDatabaseName, selectedSaveLocation)
//     }
//     else {
//       WriteToYaml('duo-inputs-column-both-advanced')
//     }
//   }


//   const parameters = {
//       dda: {},
//       dia: {},
//       annotation: {},
//       misc: {
//         dia_store_blobs: true,
//         do_dda_processing: false,
//         do_dia_processing: false,
//         do_annotation: false,
//         overwrite_annotations: false,
//         ionization: "POS"
//       }
//     };
  
//   const inputOutput = {
//     dda_data_files: [],
//     dia_data_files: [],
//     results_db: [],
//     lipid_class_scdb_config: []
//   };

//   const gui_params = {
//     db_pick: selectedDatabaseOption,
//     db_name: selectedDatabaseName,
//     save_loc: selectedSaveLocation
//   }

//   if (checkboxes.advanced.dda.checked === true) {
//     parameters.misc.do_dda_processing = true;
//   }
  
//   if (checkboxes.advanced.dia.checked === true) {
//     parameters.misc.do_dia_processing = true;
//   }

//   if (checkboxes.advanced.annotate.checked === true) {
//     parameters.misc.do_annotation = true;
//   }

//   if (isAnnotationAppend === false) {
//     parameters.misc.overwrite_annotations = true;
//   }

//   if (isIonizationPositive === false) {
//     parameters.misc.ionization = "NEG";
//   }

//   // Add in parameter values
//   for (let i = 0; i < inputs.length; i++) {
//     const input = inputs[i];
//     const input2 = inputs2[i];

//     if (input2.id === "dda" || input2.id === "dia" || input2.id === "annotation") {
//         currentHeader = input2.id;
//         continue;
//     }
 
//     if (input2.key === 'Ignore') {
//         currentSubheader = input2.id;
//         if (currentHeader && !parameters[currentHeader][currentSubheader]) {
//             parameters[currentHeader][currentSubheader] = {};
//         }
//         continue;
//     }

//     if (input && input2 && input.style.display !== 'none') {
//         if (currentHeader && currentSubheader) {
//             parameters[currentHeader][currentSubheader][input2.id] = input.value;
//         } else if (currentHeader) {
//             parameters[currentHeader][input2.id] = input.value;
//         } else {
//             parameters['misc'][input2.id] = input.value;
//         }
//     }
//   }

//   // Update files with those selected by user
//   inputOutput['dda_data_files'] = filesDDA;
//   inputOutput['dia_data_files'] = filesDIA;
//   inputOutput['results_db'] = filesDatabase[0];  // Only one file allowed

//   // Annotation File is only assigned if annotation behaivor is set to custom file.
//   if (isBehaviorDefault === true) {
//     inputOutput['lipid_class_scdb_config'] = filesAnnotation[0]; // Only one file allowed
//   }

//   console.log(gui_params)
//   const options = {
//     pythonPath: 'python3',
//     args: {
//       input_output: inputOutput,
//       params: parameters,
//       options: gui_params
//     }
//   };

//   outputBox.innerText += "Experiment Starting. Please give it one minute to begin. " + '\n';
//   window.api.send('run-python-experiment', options);
//   disableButton()
// } 




// function RunExperiment() {
//   // 1) Gather GUI inputs
//   const expName        = document.getElementById("experiment-name").value.trim();
//   const saveLoc        = document.getElementById("selected-directory").value.trim();
//   const filesDDA       = fileListToArray(fileListDDA);
//   const filesDIA       = fileListToArray(fileListDIA);
//   const filesDatabase  = fileListToArray(fileListDatabase);
//   const filesAnnotation= fileListToArray(fileListAnnotation);
//   const filesFragRules = fileListToArray(fileListFragRulesConfig);
//   const filesCcsTrends = fileListToArray(fileListCcsTrendsConfig);
//   const filesRtRange   = fileListToArray(fileListRtRangeConfig);
//   const filesSumComp   = fileListToArray(fileListSumCompConfig);

//   // 2) Basic validation
//   if (!expName || !saveLoc) {
//     alert("Please enter an experiment name and save location.");
//     return;
//   }

//   // 3) Build absolute paths for output files
//   const dbFile     = `${saveLoc}/${expName}.db`;
//   const ddaConfig  = `${saveLoc}/${expName}_dda_config.yml`;
//   const diaConfig  = `${saveLoc}/${expName}_dia_config.yml`;
//   const annConfig  = `${saveLoc}/${expName}_ann_config.yml`;

//   // 4) Define the CLI steps
//   const steps = [
//     { cmd: ["utility", "create_db", dbFile],                   desc: "Initializing results database" },
//     { cmd: ["utility", "params", "--default-dda", ddaConfig],  desc: "Generating default DDA config" },
//     // only run DDA if files were provided
//     ...(filesDDA.length
//       ? [{ cmd: ["dda", ddaConfig, dbFile, ...filesDDA], desc: "Running DDA processing" }]
//       : []),
//     { cmd: ["utility", "params", "--default-dia", diaConfig],  desc: "Generating default DIA config" },
//     ...(filesDIA.length
//       ? [{ cmd: ["dia", "process", diaConfig, dbFile, ...filesDIA], desc: "Running DIA processing" }]
//       : []),
//     { cmd: ["dia", "calibrate_ccs", dbFile, "-0.082280", "0.132301", "9"], desc: "Calibrating CCS" },
//     { cmd: ["utility", "params", "--default-ann", annConfig],  desc: "Generating default annotation config" },
//     { cmd: ["annotate", annConfig, dbFile],                    desc: "Running lipid annotation" }
//   ];

//   // 5) Kick off the IPC to run them
//   outputBox.innerText += "Starting experiment…\n";
//   window.api.send("run-lipidimea-cli-steps", { steps });

//   // 6) Prevent double‐clicks
//   disableButton();
// }




// async function RunExperiment() {
//   // 1) Gather GUI inputs
//   const expName       = document.getElementById("experiment-name").value.trim();
//   const saveLoc       = document.getElementById("selected-directory").value.trim();
//   const filesDDA      = fileListToArray(fileListDDA);
//   const filesDIA      = fileListToArray(fileListDIA);
//   const dbFile        = `${saveLoc}/${expName}.db`;

//   // 2) Validation
//   if (!expName || !saveLoc) {
//     alert("Please enter an experiment name and save location.");
//     return;
//   }
//   if (!filesDDA.length && !filesDIA.length) {
//     alert("Please select at least one DDA or DIA file.");
//     return;
//   }

//   // 3) First, write out YOUR DDA parameters from the GUI
//   //    This uses your existing WriteToYaml helper:
  
//   if (checkboxes.advanced.dda.checked) {
//     WriteCategoryYaml(
//       'duo-inputs-column-both-advanced',
//       'dda',
//       `${expName}_dda_config`,
//       saveLoc
//     );
//   }
//   if (checkboxes.advanced.dia.checked) {
//     WriteCategoryYaml(
//       'duo-inputs-column-both-advanced',
//       'dia',
//       `${expName}_dia_config`,
//       saveLoc
//     );
//   }
//   if (checkboxes.advanced.annotate.checked) {
//     WriteCategoryYaml(
//       'duo-inputs-column-both-advanced',
//       'annotation',
//       `${expName}_ann_config`,
//       saveLoc
//     );
//   }

//   // Then build your CLI steps using those YML paths…
//   const ddaConfigPath = `${saveLoc}/${expName}_dda_config.yml`;
//   const diaConfigPath = `${saveLoc}/${expName}_dia_config.yml`;
//   const annConfigPath = `${saveLoc}/${expName}_ann_config.yml`;

//   const steps = [
//     { cmd: ["utility", "create_db", dbFile],                   desc: "Initializing results database" },
//     ...(checkboxes.advanced.dda.checked
//       ? [{ cmd: ["dda", ddaConfigPath, dbFile, ...filesDDA], desc: "Running DDA processing" }]
//       : []),
//     ...(checkboxes.advanced.dia.checked
//       ? [
//           ["utility","params","--default-dia", diaConfigPath],
//           ["dia","process", diaConfigPath, dbFile, ...filesDIA]
//         ].map((cmd, i) => ({
//           cmd,
//           desc: i===0 ? "Generating default DIA config" : "Running DIA processing"
//         }))
//       : []),
//     { cmd: ["dia","calibrate_ccs", dbFile, "-0.082280","0.132301","9"], desc:"Calibrating CCS" },
//     ...(checkboxes.advanced.annotate.checked
//       ? [
//           { cmd: ["utility","params","--default-ann", annConfigPath], desc: "Generating default annotation config" },
//           { cmd: ["annotate", annConfigPath, dbFile],                   desc: "Running lipid annotation" }
//         ]
//       : [])
//   ];

//   // send off…
//   outputBox.innerText += "Starting experiment…\n";
//   window.api.send("run-lipidimea-cli-steps", { steps });
//   disableButton();
// }

async function RunExperiment() {
  // 1) Gather GUI inputs
  const expName   = document.getElementById("experiment-name").value.trim();
  const saveLoc   = document.getElementById("selected-directory").value.trim();
  const filesDDA  = fileListToArray(fileListDDA);
  const filesDIA  = fileListToArray(fileListDIA);
  const dbOption  = getSelectedDatabaseOption();  // "append", "overwrite", "create_new"
  const dbFile    = `${saveLoc}/${expName}.db`;

  const runDDA    = checkboxes.general.dda.checked || checkboxes.advanced.dda.checked;
  const runDIA    = checkboxes.general.dia.checked || checkboxes.advanced.dia.checked;
  const runAnnot  = checkboxes.general.annotate.checked || checkboxes.advanced.annotate.checked;
  const doCal     = document.querySelector('input[name="calibrate"]:checked').value === 'yes';

  // 2) Validation
  if (!expName || !saveLoc) {
    alert("Please enter an experiment name and save location.");
    return;
  }
  if (!runDDA && !runDIA && !runAnnot) {
    alert("Please select at least one of DDA, DIA, or Annotation.");
    return;
  }
  if (runDDA && !filesDDA.length) {
    alert("You selected DDA, but did not provide any DDA files.");
    return;
  }
  if (runDIA && !filesDIA.length) {
    alert("You selected DIA, but did not provide any DIA files.");
    return;
  }

  // 3) Write out config YAMLs
  if (runDDA) {
    WriteCategoryYaml("duo-inputs-column-both-advanced", "dda", `${expName}_dda_config`, saveLoc);
  }
  if (runDIA) {
    WriteCategoryYaml("duo-inputs-column-both-advanced", "dia", `${expName}_dia_config`, saveLoc);
  }
  if (runAnnot) {
    WriteCategoryYaml("duo-inputs-column-both-advanced", "annotation", `${expName}_ann_config`, saveLoc);
  }

  const ddaCfg = `${saveLoc}/${expName}_dda_config.yml`;
  const diaCfg = `${saveLoc}/${expName}_dia_config.yml`;
  const annCfg = `${saveLoc}/${expName}_ann_config.yml`;

  // 4) Build the series of CLI steps
  const steps = [];

  // 4a) Database action
  if (dbOption === "create_new") {
    steps.push({ cmd: ["utility","create_db", dbFile], desc: "Creating new DB" });
  } else if (dbOption === "overwrite") {
    steps.push({ cmd: ["utility","create_db","--overwrite", dbFile], desc: "Overwriting DB" });
  } else {
    outputBox.innerText += "Appending to existing DB\n";
  }

  // 4b) DDA
  if (runDDA) {
    steps.push({ cmd: ["dda", ddaCfg, dbFile, ...filesDDA], desc: "Running DDA" });
  }

  // 4c) DIA
  if (runDIA) {
    steps.push({ cmd: ["dia","process", diaCfg, dbFile, ...filesDIA], desc: "Running DIA" });
    if (doCal) {
      steps.push({
        cmd: ["dia","calibrate_ccs", dbFile, "-0.082280","0.132301","9"],
        desc: "Calibrating CCS"
      });
    }
  }

  // 4d) Annotation
  if (runAnnot) {
    steps.push({ cmd: ["annotate", annCfg, dbFile], desc: "Running Annotation" });
  }

  // 5) Fire it off
  outputBox.innerText += "Starting experiment…\n";
  window.api.send("run-lipidimea-cli-steps", { steps });
  disableButton();
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







/**
 * Hide everything in `container` from the header with id=startId
 * up to (but not including) the header with id=endId.
 * If endId is null or not found, hide through the end.
 * Always hide the start header itself.
 */
/**
 * Hide everything in `container` from the header with id=startId
 * up to (but _not_ including) the header with id=endId.
 * If endId is null or not found, hide through the end.
 */
function hideSection(startId, endId, container, emptyNotice) {
  const children = Array.from(container.children);
  let hiding = false;

  for (const node of children) {
    if (!hiding) {
      if (node.tagName === 'P' && node.id === startId) {
        hiding = true;    // start hiding from here
      } else {
        continue;         // not yet at the start section
      }
    }

    // Now that hiding=true, check if we've hit the next section header:
    if (endId && node.tagName === 'P' && node.id === endId) {
      break;             // stop _before_ hiding this end header
    }

    // Otherwise, hide this node
    node.style.display = 'none';
  }

  // If everything got hidden, show the “no params” notice
  emptyNotice.style.display = 'none';
}


// Handler for Calibrate button
function calibrateDIA() {
  const dbFile = `${document.getElementById('selected-directory').value}/${document.getElementById('experiment-name').value}.db`;
  window.api.send('run-lipidimea-cli-steps', {
    steps: [
      { cmd: ["dia", "calibrate_ccs", dbFile, "-0.082280", "0.132301", "9"], desc: "Calibrating CCS" }
    ]
  });
}




function UpdateCalibrateOptions() {
  const isDIA = checkboxes.general.dia.checked 
             || checkboxes.advanced.dia.checked;
  document.getElementById("calibrate-options").style.display =
    isDIA ? "flex" : "none";
}