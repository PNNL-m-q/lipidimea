const { app, BrowserWindow, ipcMain, dialog, session } = require('electron');
const path = require('path');
const { PythonShell } = require('python-shell');
const yaml = require('js-yaml');
const fs = require('fs');
const sqlite3 = require('sqlite3');
const prompt = require('electron-prompt');
const { spawn } = require('child_process');

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
  mainWindow.loadFile(path.join(__dirname, 'intro/intro.html'));


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
ipcMain.on('getDefaults', (event) => {
  const defaultsPath = path.join(__dirname, '../../lipidimea/_include/default_params.yaml');
  console.log('YAML Path:', defaultsPath);

  fs.readFile(defaultsPath, 'utf8', (err, data) => {
    if (err) {
      console.error('Error reading YAML file:', err);
      event.reply('returnDefaults', null);
      return;
    }

    try {
      const returnDefaults = yaml.load(data);
      console.log('YAML Data:', returnDefaults);
      event.reply('returnDefaults', returnDefaults);
    } catch (error) {
      console.error('Error parsing YAML file:', error);
      event.reply('returnDefaults', null);
    }
  });
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


// pyinstaller version
ipcMain.on('run-python-yamlwriter', (event, options) => {
  const inputNumber = options.args;
  let savePath;
  if (options.location && options.name) {
      // If location and name are provided, construct the save path
      savePath = path.join(options.location, options.name + ".yaml");
  } else {
      // Otherwise, use the path directly from options
      savePath = options.path;
  }
  console.log('yamlwriter input values:', inputNumber);

  // Point to the standalone executable produced by PyInstaller
  let pythonExecutable = path.join(__dirname, '../dist', 'yamlwriter');

  const spawn = require('child_process').spawn;
  const pythonProcess = spawn(pythonExecutable, [JSON.stringify(inputNumber), savePath]);

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python script result: ${data}`);
    event.reply('python-result-yamlwriter', data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });
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


// pyinstaller version
ipcMain.on('run-python-experiment', (event, options) => {
  const inputNumber = options.args;
  console.log('Experiment input values:', inputNumber);

  // Point to the standalone executable produced by PyInstaller
  let pythonExecutable = path.join(__dirname, '../dist', 'experiment');

  const pythonProcess = spawn(pythonExecutable, [JSON.stringify(inputNumber)]);

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python script result: ${data}`);
    event.reply('python-result-experiment', data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });
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

// Run main SQL Query and return results.
ipcMain.on('fetch-database-table', (event, filePath) => {
  const db = new sqlite3.Database(filePath);
  console.log("LOG: index.js: Fetch data");
    db.all(`
    SELECT 
      dda_feat_id AS "DDA Feature ID", 
      dda_f AS "DDA Data File", 
      dia_feat_id AS "DIA Feature ID", 
      dia_f AS "DIA Data File", 
      mz AS "m/z", 
      dia_rt AS RT, 
      dt AS "Arrival Time", 
      dia_decon_frag_ids, 
      dia_xic, 
      dia_atd, 
      dt AS dia_dt, 
      dia_dt_pkht, 
      dia_dt_fwhm, 
      dia_dt_psnr, 
      dia_rt_pkht, 
      dia_rt_fwhm, 
      dia_rt_psnr,
      dda_rt_pkht, 
      dda_rt_fwhm, 
      dda_rt_psnr, 
      dda_rt, 
      dda_ms2_peaks, 
      dia_ms2_peaks, 
      dia_ms1 
    FROM _CombinedFeaturesForGUI
    `, (error, data) => {
    if (error) {
      console.error('Error fetching data from the database:', error);
      event.reply('database-table-data', data, false, error.message, databasePath);
    } else {
      event.reply('database-table-data', data, false);
    }

    db.close((closeError) => {
      if (closeError) {
        console.error('Error closing the database:', closeError);
      }
    });
  });
});


// Run SQL Query to get blobs and info for decon frags
ipcMain.on('fetch-mapping-table', (event, selectedRowValue) => {
  const db = new sqlite3.Database(dbPath); // Access the global dbPath variable here
  console.log("LOG: index.js: Fetch mapping data");

  if (!selectedRowValue.diaDeconFragIds || selectedRowValue.diaDeconFragIds.trim() === "") {
    // Handle the case where diaDeconFragIds is empty or doesn't have a value
    console.error('No IDs provided for fetching mapping data.');
    event.reply('database-table-data', [], true, "No IDs provided");
    return;
  }

  const selectedIDs = selectedRowValue.diaDeconFragIds.split(' ').map(id => id.trim()).filter(Boolean);
  const placeholders = selectedIDs.map(() => '?').join(',');
  const combinedFeaturesQuery = `
  SELECT 
      c.dia_xic, 
      c.dia_atd,
      d.decon_frag_id, 
      d.mz, 
      d.xic_dist, 
      d.atd_dist, 
      d.xic, 
      d.atd 
  FROM CombinedFeatures c
  JOIN DIADeconFragments d 
  ON (' ' || c.dia_decon_frag_ids || ' ') LIKE ('% ' || d.decon_frag_id || ' %')
  WHERE d.decon_frag_id IN (${placeholders})
`;

  db.all(combinedFeaturesQuery, selectedIDs, (error, data) => {
    if (error) {
      console.error('Error fetching mapping data from the database:', error);
      event.reply('database-table-data', data, true, error.message);
    } else {
      event.reply('database-table-data', data, true);
    }

    db.close((closeError) => {
      if (closeError) {
        console.error('Error closing the database:', closeError);
      }
    });
  });
});


// Run SQL Query to get annotation table
ipcMain.on('fetch-annotation-table', (event, filePath) => {
  const db = new sqlite3.Database(filePath);
  console.log("LOG: index.js: Fetch data");

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
