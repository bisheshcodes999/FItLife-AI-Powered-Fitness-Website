(function ($) {
  $(document).ready(function () {
    $('[id^="edit_steps_button_"]').on("click", function () {
      var name = $(this).attr("id").replace("edit_steps_button_", "");
      $("#steps_modal_" + name).show();
    });

    $('[id^="cancel_steps_"]').on("click", function () {
      var name = $(this).attr("id").replace("cancel_steps_", "");
      $("#steps_modal_" + name).hide();
    });

    $('[id^="save_steps_"]').on("click", function () {
      var name = $(this).attr("id").replace("save_steps_", "");
      var steps = [];
      $("#steps_list_" + name + " .step-item").each(function () {
        var order = $(this).find(".step-order").val();
        var guide = $(this).find(".step-guide").val();
        var duration = $(this).find(".step-duration").val();
        var image = $(this).find(".step-image").val();
        var youtube = $(this).find(".step-youtube").val();
        steps.push({
          order: parseInt(order),
          guide: guide,
          duration: parseInt(duration),
          image: image,
          youtube_link: youtube,
        });
      });
      $("#id_" + name).val(JSON.stringify(steps));
      $("#steps_modal_" + name).hide();
    });

    $('[id^="add_step_"]').on("click", function () {
      var name = $(this).attr("id").replace("add_step_", "");
      var newStep = `
          <div class="step-item">
            <label>Order:</label> <input type="number" class="step-order" value="1" /><br/>
            <label>Guide:</label> <input type="text" class="step-guide" value="" /><br/>
            <label>Duration:</label> <input type="number" class="step-duration" value="1" /><br/>
            <label>Image URL:</label> <input type="text" class="step-image" value="" /><br/>
            <label>YouTube Link:</label> <input type="text" class="step-youtube" value="" /><br/>
            <button type="button" class="remove-step">Remove</button>
            <hr/>
          </div>
        `;
      $("#steps_list_" + name).append(newStep);
    });

    $(document).on("click", ".remove-step", function () {
      $(this).closest(".step-item").remove();
    });
  });
})(django.jQuery);
