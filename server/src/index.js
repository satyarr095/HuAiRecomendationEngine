import express from 'express';
import { configDotenv } from 'dotenv';
import { connectDB } from '../config/db.js';
configDotenv();
const app = express();

const PORT = process.env.PORT || 8080;
app.use(express.json());

app.listen(PORT, () => {
    connectDB();
    console.log(`Server is running on port ${PORT}`);
});