// ------------------------------------------------------------------------
// Declare All Variables
// ------------------------------------------------------------------------

// Buttons for file selection
const selectButtonDDA = document.getElementById('select-button-dda');
const selectButtonDIA = document.getElementById('select-button-dia');
const selectButtonDatabase = document.getElementById('select-button-database');
const selectButtonAnnotation = document.getElementById('select-button-annotation');
const fileInputDDA = document.getElementById('dda-file-input');
const fileInputDIA = document.getElementById('dia-file-input');
const fileInputDatabase = document.getElementById('database-file-input');
const fileInputAnnotation = document.getElementById('annotation-file-input');

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

// Load Yaml Once
let loadyamlonce = true;

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
// const saveParamsOptions = document.getElementById('save-params');

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

// Paramater Titles
const displayTitles = {
  dda        : "DDA data analysis",
  dia        : "DIA data analysis",
  annotation : "Lipid annotation",
};

const titleToHeader = {
  "DDA data analysis" : "dda",
  "DIA data analysis" : "dia",
  "Lipid annotation"  : "annotation",
};

let experimentRunning = false;


// ------------------------------------------------------------------------
// Main Functions
// ------------------------------------------------------------------------


// Switch Between Tabs in Experiments page
function openTab(evt, tabName) {
  let tabcontent, tablinks;
  tabcontent = document.getElementsByClassName('tabcontent');
  for (let i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = 'none';
  }

  tablinks = document.getElementsByClassName('tablinks-sel');
  for (let i = 0; i < tablinks.length; i++) {
      tablinks[i].className = 'tablinks';
  }

  document.getElementById(tabName).style.display = 'block';
  evt.currentTarget.className = 'tablinks-sel';
}


// Run Full Experiment
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

  // 5) Begin Experiment
  window.api.send("run-lipidimea-cli-steps", { steps });
  experimentRunning = true;
  document.getElementById('run-btn').disabled = true;
  document.getElementById('cancel-btn').disabled = false;
  outputBox.innerText += "Starting experiment…\n";
}

// Cancel an Experiment
function cancelExperiment() {
  if (!experimentRunning) return;
  window.api.send('cancel-experiment');
  document.getElementById('cancel-btn').disabled = true;
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


// Update which file upload options are available depending on checkboxes
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

  // Only show these four when annotation is on
  fragRulesRegion.style.display = isAnnotate ? "block" : "none";
  ccsTrendsRegion.style.display = isAnnotate ? "block" : "none";
  rtRangeRegion.style.display   = isAnnotate ? "block" : "none";
  sumCompRegion.style.display   = isAnnotate ? "block" : "none";
}


// // Link General and Advanced Parameters
//   function linkInputs(a, b) {
//     if (!a || !b || a === b) return;
//     const sync = (src, dst) => () => {
//       if (src.type === 'checkbox') dst.checked = src.checked;
//       else                         dst.value   = src.value;
//     };
//     ['input', 'change'].forEach(ev => {
//       a.addEventListener(ev, sync(a, b));
//       b.addEventListener(ev, sync(b, a));
//     });
//   }
  
// (function linkGeneralAndAdvanced() {
//   const genCol = document.getElementById('duo-inputs-column-both-general');
//   const advCol = document.getElementById('duo-inputs-column-both-advanced');
//   function connect(src, dest) {
//     if (!src || !dest) return;     

//     const copy = (from, to) => {
//       if (from.type === 'checkbox')     to.checked = from.checked;
//       else                              to.value   = from.value;
//     };

//     src .addEventListener('input', () => copy(src,  dest));
//     dest.addEventListener('input', () => copy(dest, src ));
//   }

//   function buildMap(col) {
//     const map = new Map();
//     col.querySelectorAll('input:not([type="hidden"])').forEach(inp => {
//       const key =
//         `${findSection(inp)}|${findSubGroup(inp) ?? ''}|${inp.id}`;
//       map.set(key, inp);
//     });
//     return map;
//   }

//   const genInputs = buildMap(genCol);
//   const advInputs = buildMap(advCol);

//   for (const [key, gInp] of genInputs) {
//     connect(gInp, advInputs.get(key));
//   }

// })();

// A series of functions to create the param elements
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
  inputElement.type = 'hidden'; 
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

// MetaData info and formatting params
function createInput(paramMeta, id, parentNode, otherTab) {
  let element;

  if (id === 'ionization') {
    const msg = document.createElement('span');
    msg.textContent = 'Select in "Run Experiment" Tab.';
    msg.style.gridColumn = '2';
    msg.style.fontStyle = 'italic';
    msg.style.alignSelf  = 'center';
    parentNode.appendChild(msg);
    return;
  }

  if (paramMeta.display_name.toLowerCase().includes(' file')) {
    const msg = document.createElement('span');
    msg.textContent = 'Select file in "File Upload" Tab.';
    msg.style.gridColumn = '2';
    msg.style.fontStyle = 'italic';
    msg.style.alignSelf  = 'center';
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
        const inputHeight = '2rem';    
        const inputPadding = '0.25rem';

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
      element = document.createElement('input');
      element.type = 'number';
      element.step = paramMeta.type === 'int' ? '1' : 'any';
      element.value = paramMeta.default ?? '';
      break;
    default:
      element = document.createElement('input');
      element.type = 'text';
      element.value = paramMeta.default ?? '';
  }
  if (paramMeta.type !== 'range') {
    element.id = id;
    element.style.gridColumn = '2';
    element.key = 'Ignore';
  } else {
    element.style.gridColumn = '2';
  }

  parentNode.appendChild(element);
}

function collectAdvancedParams(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return {};
  const sections = {};
  let currentHeader = null;
  let currentSub    = null;
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

    if (label.key === 'Ignore') {
      currentSub = key;
      sections[currentHeader][currentSub] = {};
      return;
    }
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

// Write One Category at a time to yaml config files.
function WriteCategoryYaml(containerId, categoryKey, name, saveLoc) {
  const allSections = collectAdvancedParams(containerId);
  const section     = allSections[categoryKey] || {};

  if (categoryKey === "annotation") {
    // 1) Ionization
    const ionPos = document.getElementById("ionization-positive").checked;
    section.ionization = ionPos ? "POS" : "NEG";

    // 2) Optional file‐inputs
    const insertFile = (ulId, pathSetter) => {
      const ul = document.getElementById(ulId);
      if (!ul) return;
      const files = fileListToArray(ul);
      if (files.length) pathSetter(files[0]);
    };

    // frag_rules.config
    insertFile("file-list-frag-rules-config", 
      fp => section.frag_rules = { ...(section.frag_rules||{}), config: fp });

    // ccs_trends.config
    insertFile("file-list-ccs-trends-config", 
      fp => section.ccs_trends = { ...(section.ccs_trends||{}), config: fp });

    //rt_range_config
    insertFile("file-list-rt-range-config",
      fp => section.rt_range_config = fp);

    // sum_comp.config
    insertFile("file-list-sum-comp-config",
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

  const yamlPayload = {
    display_name : displayTitles[categoryKey] ?? categoryKey,
    ...section
  };
  
  options.args = yamlPayload;
  window.api.send("write-yaml", options);

  const paths = [];
  (function collect(obj, prefix = "") {
    for (const [k, v] of Object.entries(obj)) {
      if (typeof v === "string" && /[\\/]/.test(v)) {
        paths.push(`${prefix}${k}: ${v}`);
      } else if (v && typeof v === "object") {
        collect(v, `${prefix}${k}.`);
      }
    }
  })(section);

  outputBox.innerText +=
      `Wrote ${categoryKey.toUpperCase()} config → ${saveLoc}/${name}.yaml\n`
    + (paths.length
          ? "Paths used:\n  " + paths.join("\n  ") + "\n"
          : "\n");          
}


function findSection(el) {
  let cur = el;
  while (cur) {
    if (cur.tagName === 'P' &&
        ['dda','dia','annotation','misc'].includes(cur.id))
      return cur.id;
    cur = cur.previousElementSibling;
  }
  return null;
}

function findSubGroup(el) {
  let cur = el;
  while (cur) {
    if (cur.key === 'Ignore') return cur.id;
    if (cur.tagName === 'P' &&
        ['dda','dia','annotation','misc'].includes(cur.id))
      return null;
    cur = cur.previousElementSibling;
  }
  return null;
}


function writeScalar(id, value, headerKey, subgroupKey) {
  document.querySelectorAll(`#${CSS.escape(id)}`).forEach(el => {
    if (findSection(el)  !== headerKey)  return;
    if (findSubGroup(el) !== subgroupKey) return;

    if (el.type === 'checkbox') el.checked = Boolean(value);
    else                        el.value   = value ?? '';
    el.dispatchEvent(new Event('change'));
  });
}

function writeRange(id, obj, headerKey, subgroupKey) {
  ['min','max'].forEach(suffix => {
    const sel = `#${CSS.escape(id)}_${suffix}`;
    document.querySelectorAll(sel).forEach(el => {
      if (findSection(el)  !== headerKey)  return;
      if (findSubGroup(el) !== subgroupKey) return;

      el.value = obj[suffix] ?? '';
      el.dispatchEvent(new Event('change'));
    });
  });
}

function isDefaultLeaf(node) {
  return node && typeof node === 'object' && 'default' in node;
}

function applyYaml(node, headerKey, subgroupKey = null, path = []) {
  if (node == null) return;

  if (isDefaultLeaf(node)) {
    const val = node.default;
    const id  = path.at(-1);
    if (val && typeof val === 'object' && 'min' in val && 'max' in val)
      writeRange(id, val, headerKey, subgroupKey);
    else
      writeScalar(id, val, headerKey, subgroupKey);
    return;
  }

  if (typeof node === 'object' && 'min' in node && 'max' in node) {
    writeRange(path.at(-1), node, headerKey, subgroupKey);
    return;
  }

  if (typeof node !== 'object' || Array.isArray(node)) {
    writeScalar(path.at(-1), node, headerKey, subgroupKey);
    return;
  }

  const nextSub = subgroupKey ?? path.at(-1);
  for (const [k, v] of Object.entries(node)) {
    if (['display_name','type','description','advanced'].includes(k)) continue;
    applyYaml(v, headerKey, nextSub, [...path, k]);
  }
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

  fileInput.value = null; 
}

// Function to handle checkbox change
// Hide / Unhide appropriate sections
// These sections have a bit of hard coding.
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
    hideSection('dda', 'dia', document.getElementById('duo-inputs-column-both-general'), ParamEmptyGeneral);
    hideSection('dda', 'dia', document.getElementById('duo-inputs-column-both-advanced'), ParamEmptyAdvanced);
  }
  if (!isDIA) {
    hideSection('dia', 'annotation', document.getElementById('duo-inputs-column-both-general'), ParamEmptyGeneral);
    hideSection('dia', 'annotation', document.getElementById('duo-inputs-column-both-advanced'), ParamEmptyAdvanced);
  }
  if (!isAnnotate) {
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

function UpdateExpName() {
}

// Annotation Options for experiment
function UpdateAnnotateOptions() {
  const TF = checkboxes.general.annotate.checked
  console.log("TF: ", TF)
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


function fileListToArray(fileList) {
  if (!fileList) return [];
  return Array.from(fileList.getElementsByTagName('li'))
    .map(listItem => {
      const ft = listItem.querySelector('.file-text');
      return ft && ft.dataset && ft.dataset.path;
    })
    .filter(path => Boolean(path));
}


function hideSection(startId, endId, container, emptyNotice) {
  const children = Array.from(container.children);
  let hiding = false;

  for (const node of children) {
    if (!hiding) {
      if (node.tagName === 'P' && node.id === startId) {
        hiding = true;
      } else {
        continue;
      }
    }

    if (endId && node.tagName === 'P' && node.id === endId) {
      break;             
    }
    node.style.display = 'none';
  }

  emptyNotice.style.display = 'none';
}

function UpdateCalibrateOptions() {
  const isDIA = checkboxes.general.dia.checked 
             || checkboxes.advanced.dia.checked;
  const isAnnot = checkboxes.general.annotate.checked
             || checkboxes.advanced.annotate.checked;
  document.getElementById("calibrate-options").style.display =
    isDIA ? "flex" : "none";
  
  lockCalibrate(isAnnot);

}


function lockCalibrate(lock) {
  const yes = document.getElementById('calibrate-yes');
  const no  = document.getElementById('calibrate-no');

  if (lock) {
    yes.checked  = true; 
    yes.disabled = true;
    no.disabled  = true;
  } else {
    yes.disabled = false;
    no.disabled  = false;
  }
}



// ------------------------------------------------------------------------
// Add Event listeners.
// ------------------------------------------------------------------------


// Checkbox eventlisteners
for (let type in checkboxes) {
  for (let mode in checkboxes[type]) {
      const cb = checkboxes[type][mode];
      cb.addEventListener("change", handleCheckboxChange);
      cb.addEventListener("change", UpdateFileOptions);
  }
}
document.addEventListener('DOMContentLoaded', () => {
  window.api.send('getDefaults');
  UpdateCalibrateOptions();
  document.getElementById('calibrate-yes').checked = true;
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

databaseOptions.addEventListener("change", UpdateExpName);

// Cancel Experiment Listener
document.addEventListener('DOMContentLoaded', () => {
  const viewLink = document.querySelector('nav .menu-item[href="../results/results.html"]');
  viewLink.addEventListener('click', e => {
    if (experimentRunning) {
      e.preventDefault();
      if (confirm('An experiment is still running. Cancel it and navigate away?')) {
        cancelExperiment();
        // give it a moment to kill before navigating
        setTimeout(() => window.location.href = viewLink.href, 200);
      }
    }
  });
});


// Call the synchronizeCheckboxes function when the page is loaded
document.addEventListener('DOMContentLoaded', synchronizeCheckboxes);

// Tab navigation of Experiment Page
document.addEventListener('DOMContentLoaded', () => {
document.getElementsByClassName('tablinks')[0].click();
});

// ------------------------------------------------------------------------
// Receive Data from Index.js:
// ------------------------------------------------------------------------


// Listen for main / renderer events
window.api.receive('experiment-started', () => {
});

window.api.receive('experiment-canceled', () => {
  experimentRunning = false;
  document.getElementById('run-btn').disabled = false;
  document.getElementById('cancel-btn').disabled = true;
});

window.api.receive('experiment-finished', () => {
  experimentRunning = false;
  document.getElementById('run-btn').disabled = false;
  document.getElementById('cancel-btn').disabled = true;
});


window.api.receive('file-dialog-selection', fp =>
  window.api.send('file-dialog-selection', fp)
);


window.api.receive('file-content', yamlObj => {
  if (typeof yamlObj !== 'object' || yamlObj === null) {
    alert('Selected file is not valid YAML.');
    return;
  }

  const title     = yamlObj.display_name || '';
  const headerKey = titleToHeader[title];
  if (!headerKey) {
    alert(`display_name “${title}” does not match DDA/DIA/Annotation.`);
    return;
  }
  const tree = { ...yamlObj };
  delete tree.display_name;
  applyYaml(tree, headerKey);
  // refresh show/hide logic
  handleCheckboxChange();
});


window.api.receive('directory-selected', (path) => {
  console.log("Selected directory:", path);
  document.getElementById('selected-directory').value = path;
});

// Receive Python Experiment Results to display
window.api.receive('python-result-experiment', (result) => {
  console.log('Received result:', result);
  outputBox.innerText += result; // Append the result to the output box
  scrollToBottom(outputBox);
});

window.api.receive("debug-list-paths-result", listing => {
  outputBox.innerText +=
    "\n─── directory snapshots ───\n" +
    listing +
    "\n───────────────────────────\n";
});


// Load Default Params. Create Related Elements.
window.api.receive('returnDefaults', (data) => {
  /* ----------------- guard: run once only ------------------ */
  if (!data || !loadyamlonce) return;
  loadyamlonce = false;

  data = { PARAMETERS: data };                 // keep old variable name
  const defaults = data.PARAMETERS;
  const general  = document.getElementById('duo-inputs-column-both-general');
  const advanced = document.getElementById('duo-inputs-column-both-advanced');

  /* ----------------- build the UI (unchanged) -------------- */
  Object.keys(defaults).filter(k => k !== 'misc').forEach(sectionKey => {
    const sectionMeta = defaults[sectionKey];

    // section headers
    createHeaderElement(sectionMeta.display_name, general,  sectionKey);
    createHeaderElement(sectionMeta.display_name, advanced, sectionKey);

    // walk subsections / parameters
    Object.keys(sectionMeta)
      .filter(k => k !== 'display_name')
      .forEach(subKey => {
        const node = sectionMeta[subKey];

        if (node && typeof node === 'object' && 'default' in node) {
          if (!node.advanced) {                       // General
            createParameterElement(node.display_name, subKey,
                                   node.description, general);
            createInput(node, subKey, general, advanced);
          }
          createParameterElement(node.display_name, subKey,  // Advanced
                                 node.description, advanced);
          createInput(node, subKey, advanced, general);
          return;
        }

        if (node && typeof node === 'object') {
          createSubHeaderElement(node.display_name, general,  subKey);
          createSubHeaderElement(node.display_name, advanced, subKey);

          const entries = Object.entries(node)
                                .filter(([k]) => k !== 'display_name');

          const genEntries = entries.filter(([,m]) => !m.advanced);
          const advEntries = entries;                         // all

          genEntries.forEach(([pKey, pMeta]) => {
            createParameterElement(pMeta.display_name, pKey,
                                   pMeta.description, general);
            createInput(pMeta, pKey, general, advanced);
          });

          advEntries.forEach(([pKey, pMeta]) => {
            createParameterElement(pMeta.display_name, pKey,
                                   pMeta.description, advanced);
            createInput(pMeta, pKey, advanced, general);
          });
        }
      });
  });

  /* helper: bind two inputs so both stay in sync */
  function linkInputs(a, b) {
    if (!a || !b || a === b) return;
    const sync = (src, dst) => () => {
      if (src.type === 'checkbox') dst.checked = src.checked;
      else                         dst.value   = src.value;
    };
    ['input', 'change'].forEach(ev => {
      a.addEventListener(ev, sync(a, b));
      b.addEventListener(ev, sync(b, a));
    });
  }


// Link General and Advanced Parameters
(function linkGeneralAndAdvanced() {
  const SECTION_IDS = ['dda', 'dia', 'annotation', 'misc'];
  const genCol = document.getElementById('duo-inputs-column-both-general');
  const advCol = document.getElementById('duo-inputs-column-both-advanced');

  function findSection(el) {
    for (let cur = el.previousElementSibling; cur; cur = cur.previousElementSibling) {
      if (cur.tagName === 'P' && SECTION_IDS.includes(cur.id)) {
        return cur.id;
      }
    }
    return null;
  }

  function findSubGroup(el) {
    for (let cur = el.previousElementSibling; cur; cur = cur.previousElementSibling) {
      if (cur.tagName === 'P' && cur.key === 'Ignore') return cur.id; // subgroup id
      if (cur.tagName === 'P' && SECTION_IDS.includes(cur.id)) return null;
    }
    return null;
  }

  function wire(src, dest) {
    if (!src || !dest) return;     

    const copy = (from, to) => {
      if (from.type === 'checkbox')     to.checked = from.checked;
      else                              to.value   = from.value;
    };

    src .addEventListener('input', () => copy(src,  dest));
    dest.addEventListener('input', () => copy(dest, src ));
  }

  function buildMap(col) {
    const map = new Map();
    col.querySelectorAll('input:not([type="hidden"])').forEach(inp => {
      const key =
        `${findSection(inp)}|${findSubGroup(inp) ?? ''}|${inp.id}`;
      map.set(key, inp);
    });
    return map;
  }

  const genInputs = buildMap(genCol);
  const advInputs = buildMap(advCol);

  for (const [key, gInp] of genInputs) {
    wire(gInp, advInputs.get(key));
  }

})();


});
