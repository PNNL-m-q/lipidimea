const { app, BrowserWindow, ipcMain, dialog, session } = require('electron');
const path = require('path');
const { PythonShell } = require('python-shell');
const yaml = require('js-yaml');
const fs = require('fs');
const sqlite3 = require('sqlite3');
const prompt = require('electron-prompt');
const { spawn } = require('child_process');
const { PassThrough } = require('stream');

// This variable will hold the path to the sql database in Results. 
// It is globally defined because it is called frequently.
let dbPath = null;

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

let mainWindow;

const createWindow = () => {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1200,
    webPreferences: {
      // nodeIntegration: false,
      contextIsolation: true,
      // sandbox: false,
      preload: path.join(__dirname, 'preload.js'),
    },
    
  });


  // and load the intro.html of the app.
  // mainWindow.loadFile(path.join(__dirname, 'results/results.html'));
    mainWindow.loadFile(path.join(__dirname, 'experiment/experiment.html'));



  // Open the DevTools.
  //mainWindow.webContents.openDevTools();

  // Store the current session data when switching tabs
  mainWindow.on('blur', () => {
    const currentSession = mainWindow.webContents.session;
    currentSession.flushStorageData(); // Save the current session data
  });

  // Restore the session data when the tab becomes active again
  mainWindow.on('focus', () => {
    const currentSession = mainWindow.webContents.session;
    currentSession.clearStorageData(); // Clear the current session data
    currentSession.flushStorageData(); // Restore the stored session data
  });
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow);


app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});


// ------------ Experiment Section ----------

// Load on DOM
// Get Defaults Data
// ipcMain.on('getDefaults', (event) => {
//   const defaultsPath = path.join(__dirname, '../../lipidimea/_include/default_params.yaml');
//   console.log('YAML Path:', defaultsPath);

//   fs.readFile(defaultsPath, 'utf8', (err, data) => {
//     if (err) {
//       console.error('Error reading YAML file:', err);
//       event.reply('returnDefaults', null);
//       return;
//     }

//     try {
//       const returnDefaults = yaml.load(data);
//       console.log('YAML Data:', returnDefaults);
//       event.reply('returnDefaults', returnDefaults);
//     } catch (error) {
//       console.error('Error parsing YAML file:', error);
//       event.reply('returnDefaults', null);
//     }
//   });
// });

ipcMain.on('getDefaults', async (event) => {
  try {
    // Build paths
    const includeDir = path.join(__dirname, '../../lipidimea/_include');
    const ddaPath  = path.join(includeDir, 'default_dda_params.yaml');
    const diaPath  = path.join(includeDir, 'default_dia_params.yaml');
    const annPath  = path.join(includeDir, 'default_ann_params.yaml');

    console.log('getDefaults → loading from:', ddaPath, diaPath, annPath);

    // Read & parse
    const ddaYaml = fs.readFileSync(ddaPath, 'utf8');
    const diaYaml = fs.readFileSync(diaPath, 'utf8');
    const annYaml = fs.readFileSync(annPath, 'utf8');

    const ddaDefaults = yaml.load(ddaYaml);
    const diaDefaults = yaml.load(diaYaml);
    const annDefaults = yaml.load(annYaml);

    console.log('getDefaults → ddaDefaults keys:', Object.keys(ddaDefaults));
    console.log('getDefaults → diaDefaults keys:', Object.keys(diaDefaults));
    console.log('getDefaults → annDefaults keys:', Object.keys(annDefaults));

    // Reply with the merged object
    event.reply('returnDefaults', {
      dda: ddaDefaults,
      dia: diaDefaults,
      annotation: annDefaults
    });

  } catch (err) {
    console.error('getDefaults ERROR:', err);
    event.reply('returnDefaults', null);
  }
});


// Trigger on "Save Params as file" Button
// Open dialog to enter file name and search for save directory.
ipcMain.on('request-filename-and-directory', (event) => {
  prompt({
      title: 'Parameter File Name',
      label: 'Enter the desired filename to save parameters under:',
      value: 'saved_lipidmea_params.yaml',
      type: 'input'
  }).then((fileName) => {
      if (fileName !== null) {
          dialog.showOpenDialog({
              properties: ['openDirectory']
          }).then(directoryResult => {
              if (!directoryResult.canceled && directoryResult.filePaths.length > 0) {
                  let savePath = path.join(directoryResult.filePaths[0], fileName);
                  event.reply('selected-param-save-directory', savePath);
              }
          }).catch(err => {
              console.log(err);
          });
      }
  }).catch(console.error);
});

// Open Save Directory Dialog. 
ipcMain.on('open-directory-dialog', (event) => {
  dialog.showOpenDialog({
      properties: ['openDirectory']
  }).then(result => {
      if (!result.canceled) {
          const selectedDirectory = result.filePaths[0];
          event.sender.send('directory-selected', selectedDirectory);
      }
  }).catch(err => {
      console.error("Directory selection error:", err);
  });
});


// // pyinstaller version
// ipcMain.on('run-python-yamlwriter', (event, options) => {
//   const inputNumber = options.args;
//   let savePath;
//   if (options.location && options.name) {
//       // If location and name are provided, construct the save path
//       savePath = path.join(options.location, options.name + ".yaml");
//   } else {
//       // Otherwise, use the path directly from options
//       savePath = options.path;
//   }
//   console.log('yamlwriter input values:', inputNumber);

//   // Point to the standalone executable produced by PyInstaller
//   let pythonExecutable = path.join(__dirname, '../dist', 'yamlwriter');

//   const spawn = require('child_process').spawn;
//   const pythonProcess = spawn(pythonExecutable, [JSON.stringify(inputNumber), savePath]);

//   pythonProcess.stdout.on('data', (data) => {
//     console.log(`Python script result: ${data}`);
//     event.reply('python-result-yamlwriter', data.toString());
//   });

//   pythonProcess.stderr.on('data', (data) => {
//     console.error(`Python Error: ${data}`);
//   });
// });



ipcMain.on('run-python-yamlwriter', (event, options) => {
  // Determine where to write
  const data    = options.args;
  const saveDir = options.location || null;
  const base    = options.name    || null;
  const explicitPath = options.path || null;

  let savePath;
  if (saveDir && base) {
    savePath = path.join(saveDir, base + '.yml');
  } else if (explicitPath) {
    savePath = explicitPath;
  } else {
    event.reply('python-result-yamlwriter', 'ERROR: no valid path provided to write YAML');
    return;
  }

  try {
    // Dump the object to YAML
    const yamlStr = yaml.dump(data, {
      noRefs:        true,
      sortKeys:      false,
      lineWidth:     120,
      noCompatMode:  true
    });
    // Write it out
    fs.writeFileSync(savePath, yamlStr, 'utf8');
    event.reply('python-result-yamlwriter', `Wrote parameter file to ${savePath}\n`);
  } catch (err) {
    console.error('YAML write error:', err);
    event.reply('python-result-yamlwriter', `ERROR writing YAML: ${err.message}\n`);
  }
});



// Generic function for opening dialog to select a file
ipcMain.on('open-file-dialog', (event, options) => {
  const window = BrowserWindow.getFocusedWindow();

  dialog.showOpenDialog(window, options)
    .then((result) => {
      if (!result.canceled && result.filePaths.length > 0) {
        const filePath = result.filePaths[0];
        console.log('YML Selected Path from Index:', filePath);
        event.reply('file-dialog-selection', filePath);
      }
    })
    .catch((error) => {
      console.error('Error opening file dialog:', error);
    });
});


// Is this still in use?
// ipcMain.handle('read-file-content', (event, filePath) => {
//   // Read the content of the file and return the data
//   const fileContent = readFile(filePath);
//   return fileContent;
// });


// Function to load in yaml data
function parseYaml(content) {
  try {
    const data = yaml.load(content);
    return data;
  } catch (error) {
    console.error('Error parsing YAML:', error);
    return null;
  }
}

// Read in YAML File to replace default param values.
ipcMain.on('file-dialog-selection', (event, filePath) => {
  
  // Read the content of the selected YAML file
  const fileContent = fs.readFileSync(filePath, 'utf-8');
  const yamlData = parseYaml(fileContent);

  // Send the file content back to the renderer process
  event.sender.send('file-content', yamlData);
});



// Run python script to run the lipidimea workflow
// ipcMain.on('run-python-experiment', (event, options) => {
//   const inputNumber = options.args;
//   console.log('Experiment input values:', inputNumber);

//   let pythonExecutable = path.join(__dirname, 'embeddedPythonMac', 'python3.11');
//   const pyshell = new PythonShell(path.join(__dirname, 'experiment.py'), {
//     pythonPath: pythonExecutable,
//     args: [JSON.stringify(inputNumber)], 
//   });

//   pyshell.on('message', (result) => {
//     console.log('Python script result:', result);
//     event.reply('python-result-experiment', result);
//   });

//   pyshell.end((err) => {
//     if (err) throw err;
//   });
// });


// // pyinstaller version
// ipcMain.on('run-python-experiment', (event, options) => {
//   const inputNumber = options.args;
//   console.log('Experiment input values:', inputNumber);

//   // Point to the standalone executable produced by PyInstaller
//   let pythonExecutable = path.join(__dirname, '../dist', 'experiment');

//   const pythonProcess = spawn(pythonExecutable, [JSON.stringify(inputNumber)]);

//   pythonProcess.stdout.on('data', (data) => {
//     console.log(`Python script result: ${data}`);
//     event.reply('python-result-experiment', data.toString());
//   });

//   pythonProcess.stderr.on('data', (data) => {
//     console.error(`Python Error: ${data}`);
//   });
// });

// const { spawn } = require('child_process');

// Compute the Python project root: two levels up from gui/src
const PY_PROJECT_ROOT = path.resolve(__dirname, '..', '..');

ipcMain.on('run-lipidimea-cli-steps', async (event, { steps }) => {
  for (const { cmd, desc } of steps) {
    event.reply('python-result-experiment', `\n>>> ${desc}\n`);
    try {
      await new Promise((resolve, reject) => {
        // spawn python3.12 with cwd set to the repo root
        const child = spawn(
          'python3.12',
          ['-m', 'lipidimea', ...cmd],
          { cwd: PY_PROJECT_ROOT, env: process.env }
        );

        child.stdout.on('data', data => {
          event.reply('python-result-experiment', data.toString());
        });
        child.stderr.on('data', data => {
          event.reply('python-result-experiment', data.toString());
        });
        child.on('close', code => {
          code === 0
            ? resolve()
            : reject(new Error(`${desc} failed (exit ${code})`));
        });
      });
    } catch (err) {
      event.reply('python-result-experiment', `\nERROR: ${err.message}\n`);
      return;  // stop the sequence on first error
    }
  }
  event.reply('python-result-experiment', '\nExperiment complete.\n');
});




// ------------ Results Section ----------

// Get Sql Database path when in the Results tab.
ipcMain.on('open-database-dialog', (event, options) => {
  const window = BrowserWindow.getFocusedWindow();
  console.log("LOG: Index.js open-database-dialog")
  dialog.showOpenDialog(window, options)
    .then((result) => {
      if (!result.canceled && result.filePaths.length > 0) {
        dbPath = result.filePaths[0]; // Set the global dbPath variable here
        console.log("LOG: Index.js selected-database-path", dbPath);
        event.reply('selected-database-path', dbPath);
      }
    })
    .catch((error) => {
      console.error('Error opening file dialog:', error);
    });
});

let mainTableCache = null;
let currentDbPath = null;

ipcMain.on('fetch-database-table', (event, filePath) => {
  // If the file path is different from the cached one, clear the cache.
  if (currentDbPath !== filePath) {
    mainTableCache = null;
    currentDbPath = filePath;
  }
  
  if (mainTableCache !== null) {
    console.log("Returning cached mainTable data.");
    event.reply('database-table-data', mainTableCache);
    return;
  }
  
  const db = new sqlite3.Database(filePath);
  console.log("LOG: index.js: Fetch data in 'fetch-database-table' function");
  db.all(`
    SELECT 
        dia_pre_id,
        dfile_id,
        mz,
        rt,
        rt_pkht,
        rt_psnr,
        rt_fwhm,
        dt,
        ccs,
        dt_pkht,
        dt_pkht * dt_fwhm * 0.338831 AS peak_area,
        dt_psnr,
        dt_fwhm
    FROM 
        DIAPrecursors
  `, (error, data) => {
    if (error) {
      console.error('Error fetching data from the database:', error);
      event.reply('database-table-data', data, false, error.message, filePath);
    } else {
      mainTableCache = data;
      event.reply('database-table-data', data);
    }
    db.close((closeError) => {
      if (closeError) {
        console.error('Error closing the database:', closeError);
      }
    });
  });
});







function fetchRawBlob(featId, rawType, callback) {
  // Open the database using the global dbPath.
  const db = new sqlite3.Database(dbPath);
  const query = `
    SELECT raw_data 
    FROM Raw 
    WHERE feat_id_type = 'dia_pre_id' 
      AND feat_id = ? 
      AND raw_type = ?
  `;
  db.get(query, [featId, rawType], (error, row) => {
    if (error) {
      console.error(`Error fetching ${rawType} blob for feature ${featId}:`, error);
      callback(error);
    } else {
      // Return the blob data (or null if not found)
      callback(null, row ? row.raw_data : null);
    }
    db.close();
  });
}


// IPC handler for fetching raw blob data.
ipcMain.on('fetch-raw-blob', (event, { featId, rawType }) => {
  fetchRawBlob(featId, rawType, (error, blob) => {
    if (error) {
      event.reply('raw-blob-result', { rawType, error: error.message });
    } else {
      if (blob) {
        try {
          // Convert the blob into a float array and then split it into x and y arrays.
          const floatArray = blobToFloatArray(blob);
          const unpackedData = unpackData(floatArray);
          // Send the processed data (x and y arrays) back to the renderer.
          event.reply('raw-blob-result', { rawType, data: unpackedData });
        } catch (ex) {
          console.error(`Error processing ${rawType} blob for feature ${featId}:`, ex);
          event.reply('raw-blob-result', { rawType, error: ex.message });
        }
      } else {
        // If no blob is found, reply with a null data field.
        event.reply('raw-blob-result', { rawType, data: null });
      }
    }
  });
});




// // Run SQL Query to get blobs and info for decon frags
// ipcMain.on('fetch-mapping-table', (event, selectedRowValue) => {
//   const db = new sqlite3.Database(dbPath); // Access the global dbPath variable here
//   console.log("LOG: index.js: Fetch data for 'fetch-mapping-table' function");

//   if (!selectedRowValue.diaDeconFragIds || selectedRowValue.diaDeconFragIds.trim() === "") {
//     // Handle the case where diaDeconFragIds is empty or doesn't have a value
//     console.error('No IDs provided for fetching mapping data.');
//     // event.reply('database-table-data', [], true, "No IDs provided");       # Removed this in update
//     return;
//   }

//   const selectedIDs = selectedRowValue.diaDeconFragIds.split(' ').map(id => id.trim()).filter(Boolean);
//   const placeholders = selectedIDs.map(() => '?').join(',');
//   // Old Version
//   const combinedFeaturesQuery = `
//   SELECT 
//       c.dia_xic, 
//       c.dia_atd,
//       d.decon_frag_id, 
//       d.mz, 
//       d.xic_dist, 
//       d.atd_dist, 
//       d.xic, 
//       d.atd 
//   FROM CombinedFeatures c
//   JOIN DIADeconFragments d 
//   ON (' ' || c.dia_decon_frag_ids || ' ') LIKE ('% ' || d.decon_frag_id || ' %')
//   WHERE d.decon_frag_id IN (${placeholders})
// `;
// // New code to integrate somehow
// // SELECT 
// //     raw_n,     -- number of points in the raw arrays, if that is useful, can omit otherwise
// //     raw_data   -- raw array data as BLOB
// // FROM 
// //     Raw
// // WHERE 
// //     -- <RAW_TYPE> can be one of "DIA_PRE_MS1", "DIA_PRE_XIC", "DIA_PRE_ATD", 
// //     -- "DIA_FRAG_XIC", "DIA_FRAG_ATD" depending on what data is needed
// //     -- You may need to check that a BLOB is actually returned from the 
// //     -- query, since it is not guaranteed that every DIA precursor will have
// //     -- all of the BLOB data stored (in fact, there is a parameter that controls
// //     -- whether any BLOB data is even stored in the first place)
// //     raw_type == "<RAW_TYPE>"          
// //     AND feat_id_type == "dia_pre_id"
// //     AND feat_id = <dia_precursor_id>                 -- use the DIA precursor ID to select the raw data 

//   db.all(combinedFeaturesQuery, selectedIDs, (error, data) => {
//     if (error) {
//       console.error('Error fetching mapping data from the database:', error);
//       // event.reply('database-table-data', data, true, error.message);
//     } else {
//       // event.reply('database-table-data', data, true);
//       //pass
//     }

//     db.close((closeError) => {
//       if (closeError) {
//         console.error('Error closing the database:', closeError);
//       }
//     });
//   });
// });


// Run SQL Query to get annotation table
ipcMain.on('fetch-annotation-table', (event, filePath) => {
  const db = new sqlite3.Database(filePath);
  console.log("LOG: index.js: Fetch data in 'fetch-annotation-table' function");

  db.all('SELECT * FROM Lipids', (error, data) => {
    if (error) {
      console.error('Error fetching data from the database:', error);
      event.reply('database-annotation-data', data, false, error.message, filePath);
    } else {
      event.reply('database-annotation-data', data, false);
    }

    db.close((closeError) => {
      if (closeError) {
        console.error('Error closing the database:', closeError);
      }
    });
  });
});


// Function to process Blobs
function blobToFloatArray(blob) {
  const buffer = Buffer.from(blob);
  const floatArray = [];
  for(let i = 0; i < buffer.length; i += 8) {
      floatArray.push(buffer.readDoubleLE(i));
  }
  return floatArray;
}

// Function to unpack blobs
function unpackData(floatArray) {
  const halfLength = floatArray.length / 2;
  const x = floatArray.slice(0, halfLength);
  const y = floatArray.slice(halfLength);

  return { x, y };
}

// Process blob data for decon xic and atd tables
ipcMain.on('process-decon-blob-data', (event, blobs) => {


  // This all needs to be replaced. We will need to query Raw based on something...?
  try {

    const xic = unpackData(blobToFloatArray(blobs.dia_xic));
    const atd = unpackData(blobToFloatArray(blobs.dia_atd));
    const PreXic = unpackData(blobToFloatArray(blobs.pre_dia_xic));
    const PreAtd = unpackData(blobToFloatArray(blobs.pre_dia_atd));
    const xicPairs = xic.x.map((x, i) => [x, xic.y[i]]);
    const atdPairs = atd.x.map((x, i) => [x, atd.y[i]]);
    const PreXicPairs = PreXic.x.map((x, i) => [x, PreXic.y[i]]);
    const PreAtdPairs = PreAtd.x.map((x, i) => [x, PreAtd.y[i]]);


    event.reply('return-decon-blob-data', {
      xicArray: xicPairs,
      atdArray: atdPairs,
      PreXicArray: PreXicPairs,
      PreAtdArray: PreAtdPairs
    });
  } catch (err) {
    console.error("Error processing the blob data:", err);
    event.reply('return-decon-blob-data', { error: err.message });
  }
});


// Process blob data for Arrival Time Distribution Plot
ipcMain.on('process-atd-blob-data', (event, blobs) => {
  try {
    console.log("string: ",blobs.dia_atd)
    const atd = unpackData(blobToFloatArray(blobs.dia_atd));
    console.log(atd)

    const atdPairs = atd.x.map((x, i) => [x, atd.y[i]]);

    event.reply('return-atd-blob-data', {
      atdArray: atdPairs,
    });
  } catch (err) {
    console.error("Error processing the blob data:", err);
    event.reply('return-atd-blob-data', { error: err.message });
  }
});

// Process blob data for XIC Plot
ipcMain.on('process-xic-blob-data', (event, blobs) => {
  try {
    console.log("blob: ",blobs.dia_xic)
    const xic = unpackData(blobToFloatArray(blobs.dia_xic));
    console.log(xic)

    const xicPairs = xic.x.map((x, i) => [x, xic.y[i]]);

    event.reply('return-xic-blob-data', {
      xicArray: xicPairs,
    });
  } catch (err) {
    console.error("Error processing the blob data:", err);
    event.reply('return-xic-blob-data', { error: err.message });
  }
});


// Process blob data for MS1 Plot
ipcMain.on('process-ms1-blob-data', (event, blobs) => {
  try {
    console.log("blob: ",blobs.dia_ms1)
    const ms1 = unpackData(blobToFloatArray(blobs.dia_ms1));
    console.log(ms1)

    const ms1Pairs = ms1.x.map((x, i) => [x, ms1.y[i]]);

    event.reply('return-ms1-blob-data', {
      ms1Array: ms1Pairs,
    });
  } catch (err) {
    console.error("Error processing the blob data:", err);
    event.reply('return-ms1-blob-data', { error: err.message });
  }
});






//  New DDA Work

ipcMain.on('fetch-dda-features', (event, { diaMz, tolerance }) => {
  const tol = tolerance || 0.01;
  const db = new sqlite3.Database(dbPath);
  const query = `
    SELECT 
      dda_pre_id,
      mz,
      rt AS dda_rt,
      rt_pkht AS dda_rt_pkht,
      rt_fwhm AS dda_rt_fwhm
    FROM DDAPrecursors
    WHERE mz BETWEEN ? AND ?
  `;
  db.all(query, [diaMz - tol, diaMz + tol], (error, rows) => {
    if (error) {
      console.error("Error fetching DDA features from DDAPrecursors:", error);
      event.reply('dda-features-result', { error: error.message });
    } else {
      event.reply('dda-features-result', { features: rows });
    }
    db.close();
  });
});



function fetchDDABlob(featId, blobType, callback) {
  const db = new sqlite3.Database(dbPath);
  const query = `
    SELECT raw_data
    FROM Raw
    WHERE feat_id_type = 'dda_pre_id'
      AND feat_id = ?
      AND raw_type = ?
  `;
  db.get(query, [featId, blobType], (error, row) => {
    if (error) {
      console.error(`Error fetching ${blobType} blob for DDA feature ${featId}:`, error);
      callback(error);
    } else {
      callback(null, row ? row.raw_data : null);
    }
    db.close();
  });
}

ipcMain.on('fetch-dda-blob', (event, { featId, blobType }) => {
  fetchDDABlob(featId, blobType, (error, blob) => {
    if (error) {
      event.reply('dda-blob-result', { blobType, error: error.message });
    } else {
      if (blob) {
        try {
          const floatArray = blobToFloatArray(blob);
          const unpackedData = unpackData(floatArray);
          event.reply('dda-blob-result', { blobType, data: unpackedData });
        } catch (ex) {
          console.error(`Error processing ${blobType} blob for feature ${featId}:`, ex);
          event.reply('dda-blob-result', { blobType, error: ex.message });
        }
      } else {
        event.reply('dda-blob-result', { blobType, data: null });
      }
    }
  });
});






//  New Bidirectional plot work:
ipcMain.on('fetch-dia-ms2', (event, dia_pre_id) => {
  const db = new sqlite3.Database(dbPath);
  const query = `
    SELECT dia_frag_id, fmz, fint
    FROM DIAFragments
    WHERE dia_pre_id = ?
  `;
  db.all(query, [dia_pre_id], (error, rows) => {
    if (error) {
      console.error("Error fetching DIA MS2 data:", error);
      event.reply('dia-ms2-result', { error: error.message });
    } else {
      event.reply('dia-ms2-result', { data: rows });
    }
    db.close();
  });
});

// Handler for DDA MS2 data
ipcMain.on('fetch-dda-ms2', (event, dda_pre_id) => {
  const db = new sqlite3.Database(dbPath);
  const query = `
    SELECT fmz, fint
    FROM DDAFragments
    WHERE dda_pre_id = ?
  `;
  db.all(query, [dda_pre_id], (error, rows) => {
    if (error) {
      console.error("Error fetching DDA MS2 data:", error);
      event.reply('dda-ms2-result', { error: error.message });
    } else {
      event.reply('dda-ms2-result', { data: rows });
    }
    db.close();
  });
});




//  New decon stufffff

// ---------- New: Fetch decon fragments for a given DIA precursor ----------
ipcMain.on('fetch-decon-fragments', (event, dia_pre_id) => {
  const db = new sqlite3.Database(dbPath);
  const query = `
    SELECT dia_frag_id, xic_dist, atd_dist
    FROM DIAFragments
    WHERE dia_pre_id = ?
  `;
  db.all(query, [dia_pre_id], (error, rows) => {
    if (error) {
      console.error("Error fetching decon fragments for dia_pre_id", dia_pre_id, error);
      event.reply('decon-fragments-result', { error: error.message });
    } else {
      event.reply('decon-fragments-result', { fragments: rows });
    }
    db.close();
  });
});

// ---------- New: Function to fetch blob for decon fragments (feat_id_type 'dia_frag_id') ----------
function fetchRawBlobDecon(featId, rawType, callback) {
  const db = new sqlite3.Database(dbPath);
  const query = `
    SELECT raw_data 
    FROM Raw 
    WHERE feat_id_type = 'dia_frag_id'
      AND feat_id = ?
      AND raw_type = ?
  `;
  db.get(query, [featId, rawType], (error, row) => {
    if (error) {
      console.error(`Error fetching ${rawType} blob for decon feature ${featId}:`, error);
      callback(error);
    } else {
      callback(null, row ? row.raw_data : null);
    }
    db.close();
  });
}

// ---------- New: IPC handler to fetch decon blob data ----------
ipcMain.on('fetch-decon-raw-blob', (event, { featId, rawType }) => {
  fetchRawBlobDecon(featId, rawType, (error, blob) => {
    if (error) {
      event.reply('decon-raw-blob-result', { rawType, error: error.message });
    } else {
      if (blob) {
        try {
          const floatArray = blobToFloatArray(blob);
          const unpackedData = unpackData(floatArray);
          event.reply('decon-raw-blob-result', { rawType, data: unpackedData });
        } catch (ex) {
          console.error(`Error processing ${rawType} blob for decon feature ${featId}:`, ex);
          event.reply('decon-raw-blob-result', { rawType, error: ex.message });
        }
      } else {
        event.reply('decon-raw-blob-result', { rawType, data: null });
      }
    }
  });
});






//   Delete from SQL function

// ipcMain.on('delete-diaprecursor-rows', (event, rowsArray) => {
//   if (!rowsArray || !rowsArray.length) {
//     event.reply('delete-diaprecursor-rows-result', { success: false, error: 'No rows specified' });
//     return;
//   }
//   const db = new sqlite3.Database(dbPath);
//   const placeholders = rowsArray.map(() => '?').join(',');
//   const query = `DELETE FROM DIAPrecursors WHERE dia_pre_id IN (${placeholders})`;
//   db.run(query, rowsArray, function(err) {
//     if (err) {
//       console.error('Error deleting DIAPrecursor rows:', err);
//       event.reply('delete-diaprecursor-rows-result', { success: false, error: err.message });
//     } else {
//       // Clear the cache so that future fetches re-read the updated table.
//       mainTableCache = null;
//       event.reply('delete-diaprecursor-rows-result', { success: true, changes: this.changes });
//     }
//     db.close();
//   });
// });

ipcMain.on('delete-diaprecursor-rows', (event, rowsArray) => {
  if (!rowsArray || !rowsArray.length) {
    event.reply('delete-diaprecursor-rows-result', { success: false, error: 'No rows specified' });
    return;
  }

  const db = new sqlite3.Database(dbPath);
  const prePlaceholders = rowsArray.map(() => '?').join(',');

  db.serialize(() => {
    db.run("BEGIN TRANSACTION");

    // 1. Retrieve associated fragment IDs from DIAFragments.
    db.all(`SELECT dia_frag_id FROM DIAFragments WHERE dia_pre_id IN (${prePlaceholders})`, rowsArray, (err, fragRows) => {
      if (err) {
        db.run("ROLLBACK");
        event.reply('delete-diaprecursor-rows-result', { success: false, error: err.message });
        db.close();
        return;
      }
      let fragIds = fragRows && fragRows.length > 0 ? fragRows.map(r => r.dia_frag_id) : [];

      // 2. Retrieve lipid IDs from Lipids (for use in deleting from LipidSumComp).
      db.all(`SELECT lipid_id FROM Lipids WHERE dia_pre_id IN (${prePlaceholders})`, rowsArray, (err2, lipidRows) => {
        if (err2) {
          db.run("ROLLBACK");
          event.reply('delete-diaprecursor-rows-result', { success: false, error: err2.message });
          db.close();
          return;
        }
        let lipidIds = lipidRows && lipidRows.length > 0 ? lipidRows.map(r => r.lipid_id) : [];

        // 3. Delete from DIAPrecursors.
        db.run(`DELETE FROM DIAPrecursors WHERE dia_pre_id IN (${prePlaceholders})`, rowsArray, function(err3) {
          if (err3) {
            db.run("ROLLBACK");
            event.reply('delete-diaprecursor-rows-result', { success: false, error: err3.message });
            db.close();
            return;
          }
          // 4. Delete from DIAFragments.
          db.run(`DELETE FROM DIAFragments WHERE dia_pre_id IN (${prePlaceholders})`, rowsArray, function(err4) {
            if (err4) {
              db.run("ROLLBACK");
              event.reply('delete-diaprecursor-rows-result', { success: false, error: err4.message });
              db.close();
              return;
            }
            // 5. Delete from Lipids.
            db.run(`DELETE FROM Lipids WHERE dia_pre_id IN (${prePlaceholders})`, rowsArray, function(err5) {
              if (err5) {
                db.run("ROLLBACK");
                event.reply('delete-diaprecursor-rows-result', { success: false, error: err5.message });
                db.close();
                return;
              }
              // 6. Delete from Raw for precursor data.
              db.run(`DELETE FROM Raw WHERE feat_id_type = 'dia_pre_id' AND feat_id IN (${prePlaceholders})`, rowsArray, function(err6) {
                if (err6) {
                  db.run("ROLLBACK");
                  event.reply('delete-diaprecursor-rows-result', { success: false, error: err6.message });
                  db.close();
                  return;
                }
                // 7. If there are fragIds, delete from LipidFragments and Raw (for fragment data).
                const deleteFragRelated = (callback) => {
                  if (fragIds.length > 0) {
                    const fragPlaceholders = fragIds.map(() => '?').join(',');
                    db.run(`DELETE FROM LipidFragments WHERE dia_frag_id IN (${fragPlaceholders})`, fragIds, function(err7) {
                      if (err7) {
                        callback(err7);
                        return;
                      }
                      db.run(`DELETE FROM Raw WHERE feat_id_type = 'dia_frag_id' AND feat_id IN (${fragPlaceholders})`, fragIds, function(err8) {
                        callback(err8);
                      });
                    });
                  } else {
                    callback(null);
                  }
                };

                // 8. If there are lipidIds, delete from LipidSumComp.
                const deleteLipidSumComp = (callback) => {
                  if (lipidIds.length > 0) {
                    const lipidPlaceholders = lipidIds.map(() => '?').join(',');
                    db.run(`DELETE FROM LipidSumComp WHERE lipid_id IN (${lipidPlaceholders})`, lipidIds, function(err9) {
                      callback(err9);
                    });
                  } else {
                    callback(null);
                  }
                };

                // Execute deletion for frag-related and lipid mapping in series.
                deleteFragRelated((errFrag) => {
                  if (errFrag) {
                    db.run("ROLLBACK");
                    event.reply('delete-diaprecursor-rows-result', { success: false, error: errFrag.message });
                    db.close();
                    return;
                  }
                  deleteLipidSumComp((errLipid) => {
                    if (errLipid) {
                      db.run("ROLLBACK");
                      event.reply('delete-diaprecursor-rows-result', { success: false, error: errLipid.message });
                      db.close();
                      return;
                    }
                    // 9. Commit the transaction.
                    db.run("COMMIT", function(errCommit) {
                      if (errCommit) {
                        db.run("ROLLBACK");
                        event.reply('delete-diaprecursor-rows-result', { success: false, error: errCommit.message });
                        db.close();
                        return;
                      }
                      mainTableCache = null;
                      event.reply('delete-diaprecursor-rows-result', { success: true });
                      db.close();
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  });
});



ipcMain.on('fetch-lipid-fragment-details', (event, lipidId) => {
  const db = new sqlite3.Database(dbPath);
  const query = `
      SELECT frag_rule, supports_fa, diagnostic, dia_frag_id
      FROM LipidFragments
      WHERE lipid_id = ?
  `;
  db.all(query, [lipidId], (err, rows) => {
      if (err) {
          console.error("Error fetching lipid fragments:", err);
          event.reply('lipid-fragment-details', { error: err.message });
      } else {
          event.reply('lipid-fragment-details', { lipidId, details: rows });
      }
      db.close();
  });
});



// Delete annotated feature rows (for the annotation table)
// Expects an array of lipid IDs (from column 0 of the annotation table)
ipcMain.on('delete-annotated-feature-rows', (event, lipidIds) => {
  if (!lipidIds || lipidIds.length === 0) {
    event.reply('delete-annotated-feature-rows-result', { success: false, error: 'No rows specified' });
    return;
  }
  
  // Open the database using the global dbPath.
  const db = new sqlite3.Database(dbPath);
  // Build placeholders for the SQL IN clause.
  const placeholders = lipidIds.map(() => '?').join(',');

  db.serialize(() => {
    db.run("BEGIN TRANSACTION");
    // 1. Delete from LipidFragments.
    db.run(`DELETE FROM LipidFragments WHERE lipid_id IN (${placeholders})`, lipidIds, function(err) {
      if (err) {
        db.run("ROLLBACK");
        event.reply('delete-annotated-feature-rows-result', { success: false, error: err.message });
        db.close();
        return;
      }
      // 2. Delete from LipidSumComp.
      db.run(`DELETE FROM LipidSumComp WHERE lipid_id IN (${placeholders})`, lipidIds, function(err2) {
        if (err2) {
          db.run("ROLLBACK");
          event.reply('delete-annotated-feature-rows-result', { success: false, error: err2.message });
          db.close();
          return;
        }
        // 3. Delete from Lipids.
        db.run(`DELETE FROM Lipids WHERE lipid_id IN (${placeholders})`, lipidIds, function(err3) {
          if (err3) {
            db.run("ROLLBACK");
            event.reply('delete-annotated-feature-rows-result', { success: false, error: err3.message });
            db.close();
            return;
          }
          // Commit the transaction.
          db.run("COMMIT", function(errCommit) {
            if (errCommit) {
              db.run("ROLLBACK");
              event.reply('delete-annotated-feature-rows-result', { success: false, error: errCommit.message });
              db.close();
              return;
            }
            // After successful commit, re-query the Lipids table so the renderer can update its annotation table.
            db.all('SELECT * FROM Lipids', (errFetch, rows) => {
              if (errFetch) {
                event.reply('delete-annotated-feature-rows-result', { success: true, error: errFetch.message });
              } else {
                event.reply('delete-annotated-feature-rows-result', { success: true, updatedData: rows });
              }
              db.close();
            });
          });
        });
      });
    });
  });
});
