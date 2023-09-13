// const { app, BrowserWindow, ipcMain } = require('electron');
// const path = require('path');
// const { PythonShell } = require('python-shell');

// function createWindow() {
//   const win = new BrowserWindow({
//     width: 400,
//     height: 200,
//     webPreferences: {
//     preload: path.join(__dirname, 'preload.js'),
//     contextIsolation: false, // Set to false to allow access to Node.js APIs in the renderer process
//     nodeIntegration: true // Set to true to enable access to Node.js modules in the renderer process
//     }
//   });

//   win.loadFile('index.html');
// }

// app.whenReady().then(createWindow);

// ipcMain.on('run-python', (event, options) => {

//   const inputNumber = options.args[0];
//   console.log('MAIN Input number:', inputNumber);

//   const pyshell = new PythonShell('script.py');

//   pyshell.send(inputNumber);

//   pyshell.on('message', (result) => {
//     console.log('Python script result:', result);
//     event.reply('python-result', result);
//   });

//   pyshell.end((err) => {
//     if (err) throw err;
//   });
// });

// ipcMain.on('run-python', (event, options) => {
//     const inputNumber = options.args[0];
//     console.log('MAIN Input number:', inputNumber);})