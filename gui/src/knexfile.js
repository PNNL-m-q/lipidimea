module.exports = {
    development: {
      client: 'sqlite3',
      connection: {
        filename: './example.db', // Specify the path and name of your SQLite database file
      },
      useNullAsDefault: true, // Required for SQLite
    },
  };