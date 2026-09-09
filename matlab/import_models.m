%% Import TensorFlow/Keras Models into MATLAB
% This script demonstrates how to import trained TensorFlow models
% into MATLAB for integration with the broader MATLAB pipeline.
%
% Requirements:
% - Deep Learning Toolbox
% - Deep Learning Toolbox Importer for TensorFlow Models
% - MATLAB R2021b or later

%% Import DR Classifier
fprintf('Importing DR Classifier...\n');

modelPath = '../models/aptos/saved_model';
if exist(modelPath, 'dir')
    % Import TensorFlow SavedModel
    try
        drClassifier = importTensorFlowNetwork(modelPath);
        fprintf('DR Classifier imported successfully.\n');

        % Display network architecture
        disp(drClassifier);
    catch ME
        fprintf('Import failed: %s\n', ME.message);
        fprintf('Ensure TensorFlow/Keras SavedModel exists at: %s\n', modelPath);
    end
else
    fprintf('SavedModel not found at: %s\n', modelPath);
    fprintf('Train the model first using: python training/train_aptos.py\n');
end

%% Import Vessel Segmentation Model
fprintf('\nImporting Vessel Segmentation Model...\n');

vesselPath = '../models/drive/saved_model';
if exist(vesselPath, 'dir')
    try
        vesselModel = importTensorFlowNetwork(vesselPath);
        fprintf('Vessel model imported successfully.\n');
    catch ME
        fprintf('Import failed: %s\n', ME.message);
    end
else
    fprintf('Vessel model not found at: %s\n', vesselPath);
end

%% Verify imports
fprintf('\n=== Import Summary ===\n');
if exist('drClassifier', 'var')
    fprintf('DR Classifier: Imported\n');
else
    fprintf('DR Classifier: NOT IMPORTED\n');
end

if exist('vesselModel', 'var')
    fprintf('Vessel Model: Imported\n');
else
    fprintf('Vessel Model: NOT IMPORTED\n');
end
