const { app, BrowserWindow, ipcMain, dialog, session } = require('electron');
const path = require('path');
const { PythonShell } = require('python-shell');
const yaml = require('js-yaml');
const fs = require('fs');
const sqlite3 = require('sqlite3');
const { spawn } = require('child_process');
// const { fetchData } = require('./database');

// const pythonProcess = spawn('python', ['experiment.py']);



// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

let mainWindow;

const createWindow = () => {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      // nodeIntegration: false,
      contextIsolation: true,
      // sandbox: false,
      preload: path.join(__dirname, 'preload.js'),
    },
    
  });


  // and load the index.html of the app.
  mainWindow.loadFile(path.join(__dirname, 'index.html'));


  // Open the DevTools.
  mainWindow.webContents.openDevTools();

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


// Get Defaults Data
ipcMain.on('getYamlDataBoth', (event) => {
  const yamlPathBoth = path.join(__dirname, '../../LipidIMEA/msms/default_params.yaml');
  console.log('YAML Path:', yamlPathBoth);

  fs.readFile(yamlPathBoth, 'utf8', (err, data) => {
    if (err) {
      console.error('Error reading YAML file:', err);
      event.reply('yamlDataBoth', null);
      return;
    }

    try {
      const yamlDataBoth = yaml.load(data);
      console.log('YAML Data:', yamlDataBoth);
      event.reply('yamlDataBoth', yamlDataBoth);
    } catch (error) {
      console.error('Error parsing YAML file:', error);
      event.reply('yamlDataBoth', null);
    }
  });
});


ipcMain.on('run-python-yamlwriter', (event, options) => {
  const inputNumber = options.args;
  console.log('yamlwriter input values:', inputNumber);

  const pyshell = new PythonShell(path.join(__dirname, 'yamlwriter.py'), {
    pythonPath: 'python3',
    args: [JSON.stringify(inputNumber)], // Pass the input as an array if required by the Python script
  });

  pyshell.on('message', (result) => {
    console.log('Python script result:', result);
    event.reply('python-result-yamlwriter', result);
  });

  pyshell.end((err) => {
    if (err) throw err;
  });
});

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


ipcMain.handle('read-file-content', (event, filePath) => {
  // Read the content of the file and return the data
  const fileContent = readFile(filePath);
  return fileContent;
});


function parseYaml(content) {
  try {
    const data = yaml.load(content);
    return data;
  } catch (error) {
    console.error('Error parsing YAML:', error);
    return null;
  }
}

// Define the 'file-dialog-selection' IPC handler
ipcMain.on('file-dialog-selection', (event, filePath) => {
  
  // Read the content of the selected YAML file
  const fileContent = fs.readFileSync(filePath, 'utf-8');
  const yamlData = parseYaml(fileContent);

  // Send the file content back to the renderer process
  event.sender.send('file-content', yamlData);
});



// Run Experiment
ipcMain.on('run-python-experiment', (event, options) => {
  const inputNumber = options.args;
  console.log('Experiment input values:', inputNumber);

  const pyshell = new PythonShell(path.join(__dirname, 'experiment.py'), {
    pythonPath: 'python3',
    args: [JSON.stringify(inputNumber)], // Pass the input as an array if required by the Python script
  });

  pyshell.on('message', (result) => {
    console.log('Python script result:', result);
    event.reply('python-result-experiment', result);
  });

  pyshell.end((err) => {
    if (err) throw err;
  });
});



let filePath = null; // Variable to store the selected database file path

ipcMain.on('open-database-dialog', (event, options) => {
  const window = BrowserWindow.getFocusedWindow();
  console.log("LOG: Index.js open-database-dialog")
  dialog.showOpenDialog(window, options)
    .then((result) => {
      if (!result.canceled && result.filePaths.length > 0) {
        filePath = result.filePaths[0]; // Store the selected file path
        console.log("LOG: Index.js selected-database-path", filePath);
        event.reply('selected-database-path', filePath);
      }
    })
    .catch((error) => {
      console.error('Error opening file dialog:', error);
    });
});

ipcMain.on('fetch-database-table', (event, filePath) => {
  const db = new sqlite3.Database(filePath);
  console.log("LOG: index.js: Fetch data");

  // db.all('SELECT dda_feat_id AS "DDA Feature ID", dda_f AS "DDA Data File", dia_feat_id AS "DIA Feature ID", dia_f AS "DIA Data File" ,mz AS "m/z", dia_rt AS RT, dt AS "Arrival Time", dia_decon_frag_ids, dia_xic,dia_dt,dia_dt_pkht,dia_dt_fwhm,dia_dt_psnr FROM CombinedFeatures', (error, data) => {
  db.all('SELECT dda_feat_id AS "DDA Feature ID", dda_f AS "DDA Data File", dia_feat_id AS "DIA Feature ID", dia_f AS "DIA Data File" ,mz AS "m/z", dia_rt AS RT, dt AS "Arrival Time", dia_decon_frag_ids, dia_xic, dia_atd, dt AS dia_dt, dia_dt_pkht, dia_dt_fwhm, dia_dt_psnr, dia_rt_pkht, dia_rt_fwhm, dia_rt_psnr,dda_rt_pkht, dda_rt_fwhm, dda_rt_psnr, dda_rt, dda_ms2_peaks, dia_ms2_peaks, dia_ms1 FROM CombinedFeatures', (error, data) => {
    if (error) {
      console.error('Error fetching data from the database:', error);
      event.reply('database-table-data', data, false, error.message, filePath);
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



ipcMain.on('fetch-mapping-table', (event, selectedRowValue) => {
  const db = new sqlite3.Database(filePath); // Access the filePath variable here
  console.log("LOG: index.js: Fetch mapping data");

  if (!selectedRowValue.diaDeconFragIds || selectedRowValue.diaDeconFragIds.trim() === "") {
    // Handle the case where diaDeconFragIds is empty or doesn't have a value
    console.error('No IDs provided for fetching mapping data.');
    event.reply('database-table-data', [], true, "No IDs provided");
    return;
    
  }

  // Convert diaDeconFragIds to an array by splitting on spaces
  const selectedIDs = selectedRowValue.diaDeconFragIds.split(' ').map(id => id.trim()).filter(Boolean);

  // Create placeholders for SQLite query based on the number of IDs.
  const placeholders = selectedIDs.map(() => '?').join(',');

  // Update the query to use the IN clause.
  // const query = `SELECT decon_frag_id, mz, xic_dist, atd_dist, xic, atd FROM DIADeconFragments WHERE decon_frag_id IN (${placeholders})`;

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



ipcMain.on('process-blob-data', (event, blobs) => {
  try {

    const xic = unpackData(blobToFloatArray(blobs.dia_xic));
    const atd = unpackData(blobToFloatArray(blobs.dia_atd));
    const PreXic = unpackData(blobToFloatArray(blobs.pre_dia_xic));
    const PreAtd = unpackData(blobToFloatArray(blobs.pre_dia_atd));

    const xicPairs = xic.x.map((x, i) => [x, xic.y[i]]);
    const atdPairs = atd.x.map((x, i) => [x, atd.y[i]]);
    const PreXicPairs = PreXic.x.map((x, i) => [x, PreXic.y[i]]);
    const PreAtdPairs = PreAtd.x.map((x, i) => [x, PreAtd.y[i]]);


    event.reply('processed-4-blob-data', {
      xicArray: xicPairs,
      atdArray: atdPairs,
      PreXicArray: PreXicPairs,
      PreAtdArray: PreAtdPairs
    });
  } catch (err) {
    console.error("Error processing the blob data:", err);
    event.reply('processed-4-blob-data', { error: err.message });
  }
});


ipcMain.on('process-blob-data-mid-bot', (event, blobs) => {
  try {
    console.log("string: ",blobs.dia_atd)
    const atd = unpackData(blobToFloatArray(blobs.dia_atd));
    console.log(atd)
    // const atd = unpackData(blobs.dia_atd);

    const atdPairs = atd.x.map((x, i) => [x, atd.y[i]]);

    event.reply('processed-blob-data-mid-bot', {
      atdArray: atdPairs,
    });
  } catch (err) {
    console.error("Error processing the blob data:", err);
    event.reply('processed-blob-data-mid-bot', { error: err.message });
  }
});


ipcMain.on('process-blob-data-mid-top', (event, blobs) => {
  try {
    console.log("blob: ",blobs.dia_xic)
    const xic = unpackData(blobToFloatArray(blobs.dia_xic));
    console.log(xic)

    const xicPairs = xic.x.map((x, i) => [x, xic.y[i]]);

    event.reply('processed-blob-data-mid-top', {
      xicArray: xicPairs,
    });
  } catch (err) {
    console.error("Error processing the blob data:", err);
    event.reply('processed-blob-data-mid-top', { error: err.message });
  }
});



ipcMain.on('process-blob-data-left-top', (event, blobs) => {
  try {
    console.log("blob: ",blobs.dia_ms1)
    const ms1 = unpackData(blobToFloatArray(blobs.dia_ms1));
    console.log(ms1)

    const ms1Pairs = ms1.x.map((x, i) => [x, ms1.y[i]]);

    event.reply('processed-blob-data-left-top', {
      ms1Array: ms1Pairs,
    });
  } catch (err) {
    console.error("Error processing the blob data:", err);
    event.reply('processed-blob-data-left-top', { error: err.message });
  }
});

function blobToFloatArray(blob) {
  const buffer = Buffer.from(blob);
  const floatArray = [];
  for(let i = 0; i < buffer.length; i += 8) {
      floatArray.push(buffer.readDoubleLE(i));
  }
  
  return floatArray;
}


function unpackData(floatArray) {
  const halfLength = floatArray.length / 2;
  const x = floatArray.slice(0, halfLength);
  const y = floatArray.slice(halfLength);

  return { x, y };
}



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