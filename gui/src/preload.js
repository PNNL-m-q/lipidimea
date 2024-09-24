const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  send: (channel, data) => {
    ipcRenderer.send(channel, data);
    console.log('Preload Send:', channel, data);
  },
  receive: (channel, func) => {
    ipcRenderer.on(channel, (event, ...args) => func(...args));
    console.log('Preload Receive:', channel);
  },
});

