// const knex = require('knex');
// const config = require('./knexfile');

// // Initialize Knex with the development configuration
// const db = knex(config.development);

// // Function to fetch data from the database
// // Fetch data function with additional logging
// async function fetchData() {
//     try {
//       const query = db.select('*').from('DDAFeatures');
//       console.log('Generated query:', query.toString()); // Print the generated query
//       const data = await query;
//       console.log('DB Table:', data);
//       return data;
//     } catch (error) {
//       console.error('Error fetching data:', error);
//       throw error;
//     }
//   }
  
// module.exports = {
//   fetchData,
// };

