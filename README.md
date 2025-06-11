# Healthcare Resource Allocation
## Big Data Technologies Project

The primary goal of the application is to provide a comprehensive, data-driven view of the Australian healthcare ecosystem, revealing trends and variations in resource utilisation across hospitals and regions.

<br>

<p align="center">
  <img src="https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/blob/7da3dd9f425534fce06b3f21a67059a9697cf7b8/logo.png?raw=true" width="400"/>  
</p>

Designed for government decision-makers, this app enables informed policy-making by providing a clear, real-time snapshot of healthcare performance.

## Contents:
1. [Project Structure](https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/tree/main?tab=readme-ov-file#project-structure)
2. [Getting Started](https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/tree/main?tab=readme-ov-file#getting-started)
3. [Workflow](https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/tree/main?tab=readme-ov-file#workflow)
4. [Dashboard Demo](https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/tree/main?tab=readme-ov-file#dashboard-demo)
5. [Data Sources](https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/tree/main?tab=readme-ov-file#data-sources)
6. [Authors](https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/tree/main?tab=readme-ov-file#authors)


## 1. Project Structure
```
.
├── LICENSE
├── README.md
├── data
│   ├── Admitted Patients.xlsx
│   ├── Expediture.xlsx
│   ├── Hospital-resources-tables-2022-23.xlsx
│   ├── images
│   │   └── logo.png
│   └── myhosp-mapping-details-extract.xlsx
├── docker-compose.yml
├── dockerfiles
│   ├── Dockerfile
│   ├── Dockerfile2
│   └── Dockerfile3
├── media
│   ├── ABS_logo.jpeg
│   ├── AIHW_logo.png
│   ├── Dashboard budget.gif
│   ├── Dashboard demo.gif
│   ├── Dashboard hospitals.gif
│   ├── Dashboard measures.gif
│   └── logo.png
├── run.sh
└── src
    ├── app
    │   ├── dashboard.py
    │   └── requirements_dashboard.txt
    └── processing
        ├── ETL.py
        ├── jars
        │   └── postgresql-42.7.3.jar
        ├── requirements_spark.txt
        ├── setup.py
        └── utilities
            ├── budget_lm.py
            ├── tables.py
            ├── tools.py
            ├── values.py
            └── values_lm.py
```

The repository is organized into several key directories and files:

- **`data/`**: This folder contains all the relevant datasets in Excel format, along with an `images/` subdirectory for logos and other visual assets.

- **`dockerfiles/`**: Contains multiple Dockerfiles to support the various environments required by the project.

- **`media/`**: Includes media assets such as logos, workflow diagrams, and animated GIFs demonstrating the dashboard features.

- **`src/`**: The core source code is located here. It is divided into:
  - **`app/`**: Contains the dashboard application script and its dependencies.
  - **`processing/`**: ETL scripts, utility functions, and supporting libraries, including JAR files for data processing.

- **Root Files**: 
  - `LICENSE`: The licensing information for the project.
  - `README.md`: The main documentation file.
  - `docker-compose.yml`: Configuration file for Docker Compose to orchestrate the containerized environment.
  - `run.sh`: A shell script to execute the project setup.

## 2. Getting Started

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/SoniaBorsi/Healthcare-Resource-Allocation.git
   cd Healthcare-Resource-Allocation
2. **Run the application**:
   ```bash
   bash run.sh
3. **Wait for the the data to be loaded into the db**
   This usually takes about 1 hour, depending on your internet connection
4. **Access the dashboard**
   Got to localhost:8080 and explore all the analytics

Note: It is recommended that the dashboard is run once the data storing process is complete, in line with the current project status. This will be improved in a future update.


## 3. Workflow
The development of the Australian Efficient Resource Allocation App has been supported by a carefully selected suite of big data technologies, each chosen for its ability to address specific aspects of the system's architecture.

<p align="center">
  <img src="https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/blob/37bea7b0cef33684c724d18915b2af0d80de200c/media/BDT%20Diagram.png?raw=true" width="600"/>  
</p>

These technologies work seamlessly together to create a robust, scalable application capable of efficiently processing large volumes of health data. 

## 4. Data Sources

Healthcare data utilized in this project is primarily extracted from the [Australian Institute of Health and Welfare (AIHW) API](https://www.aihw.gov.au/reports-data/myhospitals/content/api), an open and freely accessible resource. The available data includes:

- **Hospital Data**
- **Multi-Level Data**
- **Geographic Data**

In addition, this project integrates healthcare data with supplementary datasets provided by the [Australian Bureau of Statistics (ABS)](https://www.abs.gov.au) to enrich the analysis and ensure comprehensive insights.

<br>

<p align="center">
  <img src="https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/blob/5bb61624bfaddd9e336dd68eefd9d855e7db5a79/AIHW_logo.png?raw=true" width="400"/>  
</p>


## 5. Dashboard Demo
This application is designed to facilitate healthcare resource allocation through data-driven insights. Navigate through the various sections using the sidebar to explore different metrics and tools available to you:

<p align="center">
  <img src="https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/blob/dbae5fe6ec43d075a8c1b61d76fe9a312faec0ae/Dashboard%20demo.gif?raw=true" width="512"/>  
</p>

- **Measures**: for detailed metrics for various healthcare measures across different states in Australia
<p align="center">
  <img src="https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/blob/b9d838cc5ddf62201667c8bbc80f4005dc64ebe5/Dashboard%20measures.gif?raw=true" width="512"/>  
</p>

- **Hospitals**: for a comprehensive analysis of hospitals across different states
<p align="center">
  <img src="https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/blob/b9d838cc5ddf62201667c8bbc80f4005dc64ebe5/Dashboard%20hospitals.gif?raw=true" width="512"/>  
</p>

- **Budget**: for a a comprehensive visual analysis of healthcare expenditure data
<p align="center">
  <img src="https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/blob/b9d838cc5ddf62201667c8bbc80f4005dc64ebe5/Dashboard%20budget.gif?raw=true" width="512"/>  
</p>

More details can be found on our [paper](https://github.com/SoniaBorsi/Healthcare-Resource-Allocation/blob/f7a71216ad9e1f6794c3276f8551c0be0cbfeae4/Paper.pdf).


## 6. Authors

- [Borsi Sonia](https://github.com/SoniaBorsi/)
- [Filippo Costamagna](https://github.com/pippotek)
