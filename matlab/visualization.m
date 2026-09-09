%% Visualization of DR Screening Results
% Visualizes predictions, Grad-CAM, and evidence.
%
% Requirements:
% - Image Processing Toolbox
% - Computer Vision Toolbox

function visualization(imgPath, prediction, probabilities, gradcamMap)
    % Visualize DR screening results.
    %
    % Input:
    %   imgPath - Path to fundus image
    %   prediction - Predicted DR grade
    %   probabilities - Class probabilities
    %   gradcamMap - Grad-CAM heatmap (optional)

    % Read original image
    img = imread(imgPath);

    % Create figure
    figure('Name', 'DR Screening Results', 'NumberTitle', 'off');

    % Subplot 1: Original image
    subplot(2, 3, 1);
    imshow(img);
    title('Original Fundus');

    % Subplot 2: Prediction
    subplot(2, 3, 2);
    classNames = {'No DR', 'Mild DR', 'Moderate DR', 'Severe DR', 'Proliferative DR'};
    bar(probabilities);
    set(gca, 'XTickLabel', classNames);
    xtickangle(45);
    title(sprintf('Prediction: Grade %d', prediction));
    ylabel('Probability');

    % Subplot 3: Grad-CAM (if provided)
    subplot(2, 3, 3);
    if nargin >= 4 && ~isempty(gradcamMap)
        % Resize Grad-CAM to image size
        gradcamResized = imresize(gradcamMap, [size(img, 1), size(img, 2)]);

        % Create heatmap overlay
        heatmap = ind2rgb(im2uint8(mat2gray(gradcamResized)), jet(256));

        % Overlay on original
        overlay = imadd(img, im2uint8(heatmap * 0.4));
        imshow(overlay);
        title('Grad-CAM Overlay');
    else
        imshow(img);
        title('Grad-CAM (Not Available)');
    end

    % Subplot 4: Quality metrics (placeholder)
    subplot(2, 3, 4);
    text(0.5, 0.5, 'Quality Assessment\n(Available via pipeline)', ...
        'HorizontalAlignment', 'center', 'FontSize', 12);
    axis off;
    title('Image Quality');

    % Subplot 5: Referable DR status
    subplot(2, 3, 5);
    if prediction >= 2
        text(0.5, 0.7, 'REFERABLE', 'Color', 'r', 'FontSize', 16, ...
            'HorizontalAlignment', 'center', 'FontWeight', 'bold');
        text(0.5, 0.3, 'Level 2+', 'FontSize', 12, 'HorizontalAlignment', 'center');
    else
        text(0.5, 0.7, 'NON-REFERABLE', 'Color', 'g', 'FontSize', 16, ...
            'HorizontalAlignment', 'center', 'FontWeight', 'bold');
        text(0.5, 0.3, 'Routine follow-up', 'FontSize', 12, 'HorizontalAlignment', 'center');
    end
    axis off;
    title('Referable DR Status');

    % Subplot 6: Disclaimer
    subplot(2, 3, 6);
    text(0.5, 0.5, {'AI-assisted screening result.', ...
        'Not a definitive diagnosis.', ...
        'Clinical review required.'}, ...
        'HorizontalAlignment', 'center', 'FontSize', 10, ...
        'FontStyle', 'italic');
    axis off;
    title('Disclaimer');

    sgtitle('Diabetic Retinopathy Screening Results');
end
