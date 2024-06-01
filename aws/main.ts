import { simulator } from "./wrapper";

console.log("ENV", JSON.stringify(process.env));

const requiredParams = ["INPUT", "OUTPUT", "IGNITION_LAT", "IGNITION_LONG"];

for(const p of requiredParams) {
    if (!process.env[p]) {
        throw new Error("Missing ENV " + p);
    }
}

simulator({
    inputInstanceFolder: process.env["INPUT"]!,
    outputFolder: process.env["OUTPUT"]!,
    ignitionPoint: {
        latitude: parseFloat(process.env["IGNITION_LAT"]!),
        longitude: parseFloat(process.env["IGNITION_LONG"]!)
    }
}).then(() => {
    console.log("done");
});