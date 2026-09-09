%% DR Classification Inference in MATLAB
% Runs inference using imported TensorFlow model.
%
% Requirements:
% - Deep Learning Toolbox
% - Imported TensorFlow model

function [prediction, probabilities] = inference(imgPath, model)
    % Run DR classification inference.
    %
    % Input:
    %   imgPath - Path to fundus image
    %   model - Imported TensorFlow network (optional)
    %
    % Output:
    %   prediction - Predicted DR grade (0-4)
    %   probabilities - Class probabilities

    % Preprocess image
    img = preprocessing(imgPath);

    % Load model if not provided
    if nargin < 2
        modelPath = '../models/aptos/saved_model';
        if exist(modelPath, 'dir')
            model = importTensorFlowNetwork(modelPath);
        else
            error('Model not found. Train first.');
        end
    end

    % Run prediction
    [prediction, scores] = classify(model, img);

    % Convert to probabilities
    probabilities = double(scores);

    % Class names
    classNames = {'No DR', 'Mild DR', 'Moderate DR', 'Severe DR', 'Proliferative DR'};

    % Display results
    fprintf('\n=== DR Classification Results ===\n');
    fprintf('Predicted Grade: %d - %s\n', prediction, classNames{prediction});
    fprintf('Confidence: %.1f%%\n', max(probabilities) * 100);

    fprintf('\nProbability Distribution:\n');
    for i = 1:5
        fprintf('  Grade %d (%s): %.1f%%\n', i-1, classNames{i}, probabilities(i) * 100);
    end

    % Referable DR check
    if prediction >= 2
        fprintf('\nREFERABLE DR: YES (Level 2+)\n');
        fprintf('Recommendation: Refer for ophthalmologist review.\n');
    else
        fprintf('\nREFERABLE DR: NO\n');
    end

    fprintf('\nNOTE: AI-assisted screening result. Not a definitive diagnosis.\n');
end
