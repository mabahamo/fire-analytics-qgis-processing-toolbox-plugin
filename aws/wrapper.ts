import { tmpdir } from "node:os";
import { sep } from "node:path";
import { mkdtempSync, existsSync, mkdtemp } from "fs";

const util = require("util");
const exec = util.promisify(require("child_process").exec);

const tmpDir = tmpdir();


type ParamsType = {
  inputInstanceFolder: string;
  outputFolder: string;
  ignitionPoint: {
    latitude: number;
    longitude: number;
  }
}

export async function simulator(params: ParamsType) {
  const sourceFolder = mkdtempSync(`${tmpDir}${sep}`);
  const targetFolder = sourceFolder + "/results";
  const source = params.inputInstanceFolder;
  const target = params.outputFolder;

  const ignitionLayer = `${targetFolder}/ignitionPoint.gpkg`;

  const ignitionLayerCmd = `python3 /usr/local/Cell2FireWrapper/layer.py --latitude ${params.ignitionPoint.latitude} --longitude ${params.ignitionPoint.longitude} --output ${ignitionLayer}`
  const ignitionLayerResult = await exec(ignitionLayerCmd);
  console.log({ignitionLayerResult: ignitionLayerResult});


  const cell2FireArgs: any = { 
    "input-instance-folder": sourceFolder,
    "output-folder": targetFolder,
    "sim": "K",
    "nsims": 2,
    "seed": 123,
    "nthreads": 7,
    "fmc": 66,
    "scenario": 2,
    "weather": "rows",
    
   };

  console.log({cell2FireArgs});

  const parameters: string[] = [];

  for (const key of Object.keys(cell2FireArgs)) {
    parameters.push(`--${key} ${cell2FireArgs[key]}`);
  }


  console.log(`starting download ${source}`);
  await exec(`aws s3 cp ${source} ${sourceFolder} --recursive`);
  console.log(`downloaded ${source}`);

  /** 
   * ./Cell2Fire.Darwin.x86_64 
   * --final-grid 
   * --grids 
   * --sim K 
   * --nsims 2 
   * --seed 123 
   * --nthreads 7 
   * --fmc 66 
   * --scenario 2 
   * --weather rows 
   * --input-instance-folder /private/var/folders/0h/lvjhgtts0x32217c7ngfxfn00000gn/T/processing_CngDaM/04acfd74040d4cf2b0b572eb457cf80b/InstanceDirectory 
   * --output-folder /private/var/folders/0h/lvjhgtts0x32217c7ngfxfn00000gn/T/processing_CngDaM/04acfd74040d4cf2b0b572eb457cf80b/InstanceDirectory/results 
  */

  const cmd = `Cell2Fire --final-grid --grids --out-crown ${parameters.join(" ")}`;
  console.log({ cmd });

  const output = await exec(cmd);
  console.log({ output });

  const sampleScarFile = `${targetFolder}/Grids/Grids1/ForestGrid0.csv`;
  if (!existsSync(sampleScarFile)) {
    throw new Error(`Invalid sample scar file ${sampleScarFile}`)
  }

  /**
   * qgis_process run fire2a:scar 
   * --distance_units=meters 
   * --area_units=m2 
   * --ellipsoid=EPSG:7030 
   * --BaseLayer=/Users/mabahamo/Downloads/k/elevation.asc 
   * --SampleScarFile=/Users/mabahamo/Downloads/k/results/Grids/Grids1/ForestGrid0.csv 
   * --ScarRaster=/tmp/finalScar.tif 
   * --ScarPolygon=/tmp/scars.gpkg 
   * --BurnProbability=TEMPORARY_OUTPUT
   * 
   * { 'BaseLayer' : '/Users/mabahamo/Downloads/k/elevation.asc', 
   * 'BurnProbability' : 'TEMPORARY_OUTPUT', 
   * 'SampleScarFile' : '/Users/mabahamo/Downloads/k/results/Grids/Grids1/ForestGrid0.csv', 
   * 'ScarPolygon' : '/tmp/scars.gpkg', 
   * 'ScarRaster' : '/tmp/finalScar.tif' }
   */

  let baseLayer = `${sourceFolder}/fuels.tif`;
  if (!existsSync(baseLayer)){
    baseLayer = `${sourceFolder}/fuels.asc`;
    if (!existsSync(baseLayer)) {
      throw new Error(`"Base layer not found in ${sourceFolder}/fuels.{asc|tif}`);
    }
  }

  const scarPolygon = `${targetFolder}/scars.gpkg`;
  const scarRaster = `${targetFolder}/scarRaster.tif`;
  const fireScarCmd = `qgis_process run fire2a:scar --distance_units=meters --area_units=m2 --ellipsoid=EPSG:32718 --BaseLayer=${baseLayer} --BurnProbability=TEMPORARY_OUTPUT --SampleScarFile=${sampleScarFile} --ScarPolygon=${scarPolygon} --ScarRaster=${scarRaster}`
  console.log({fireScarCmd});

  const fireScar = await exec(fireScarCmd);
  console.log(`out: ${fireScar.stdout}\n\nerr: ${fireScar.stderr}`);

  const fireScarRasterPngCmd = `python3 /usr/local/Cell2FireWrapper/tiff_to_png.py ${scarRaster} ${targetFolder}/raster.png`
  const fireScarRasterPng = await exec(fireScarRasterPngCmd);
  console.log({fireScarRasterPng: fireScarRasterPng});

  const fireScarPngCmd = `python3 /usr/local/Cell2FireWrapper/gpkg_to_png.py ${scarPolygon} ${targetFolder}/polygon.png`
  const fireScarPng = await exec(fireScarPngCmd);
  console.log({fireScarPng: fireScarPng});


  //TODO: These files should be compressed before uploading to S3

  console.log(`starting upload ${sourceFolder} -> ${target}`);
  const ls = await exec(`find ${sourceFolder}`);
  console.log("ls: " + ls.stdout);
  await exec(`aws s3 cp ${sourceFolder} ${target} --recursive`);
  console.log(`uploaded to ${target}`);
}


