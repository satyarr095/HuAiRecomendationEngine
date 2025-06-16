import mongoose from "mongoose"

export const connectDB = async () => {
    try {
        const conn = await mongoose.connect(process.env.MONGO_URI);
        console.log(`MongoDb connected to : ${conn.connection.host}`)
    } catch (error) {
        console.log(`Error : ${error.message}`);
        process.exit(1);//code 1 means a fail, 0 is success 
    }
}