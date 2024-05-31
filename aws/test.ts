import { simulator } from "./wrapper";

simulator({
    inputInstanceFolder: "s3://b9-cell2fire-simulations-development/tif/Portezuelo/",
    outputFolder: "s3://b9-cell2fire-simulations-development/out/test/",
    ignitionPoint: {
        latitude: -33.7,
        longitude: -70.2
    }
}).then(() => {
    console.log("done");
});